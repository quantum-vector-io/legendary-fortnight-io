/**
 * Avatar Orchestration API
 *
 * ASP.NET Core Web API that coordinates all avatar services:
 * - Receives user input (text/audio)
 * - Routes to Copilot Studio or Azure OpenAI
 * - Generates speech with visemes
 * - Broadcasts to clients via SignalR
 * - Manages session state in Cosmos DB
 */

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Azure.AI.OpenAI;
using Azure.Communication.Identity;
using Microsoft.CognitiveServices.Speech;
using Microsoft.Azure.Cosmos;
using System.Text.Json;

namespace AvatarOrchestration.API;

// ============================================
// MODELS
// ============================================

public record ConversationRequest(
    string UserId,
    string Message,
    string? Language = "en-US",
    Dictionary<string, object>? Context = null
);

public record ConversationResponse(
    string ResponseText,
    List<VisemeData> Visemes,
    string AudioUrl,
    Dictionary<string, object> Metadata
);

public record VisemeData(
    int VisemeId,
    long AudioOffset
);

public class ConversationSession
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string UserId { get; set; } = string.Empty;
    public List<Message> History { get; set; } = new();
    public Dictionary<string, object> Context { get; set; } = new();
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime LastActivity { get; set; } = DateTime.UtcNow;
}

public record Message(string Role, string Content, DateTime Timestamp);

// ============================================
// SIGNALR HUB
// ============================================

public class AvatarHub : Hub
{
    private readonly ILogger<AvatarHub> _logger;

    public AvatarHub(ILogger<AvatarHub> logger)
    {
        _logger = logger;
    }

    public async Task JoinSession(string sessionId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, sessionId);
        _logger.LogInformation($"Client {Context.ConnectionId} joined session {sessionId}");
    }

    public async Task LeaveSession(string sessionId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, sessionId);
        _logger.LogInformation($"Client {Context.ConnectionId} left session {sessionId}");
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation($"Client {Context.ConnectionId} disconnected");
        await base.OnDisconnectedAsync(exception);
    }
}

// ============================================
// SERVICES
// ============================================

public interface IAvatarOrchestrator
{
    Task<ConversationResponse> ProcessMessageAsync(
        string sessionId,
        ConversationRequest request,
        CancellationToken cancellationToken = default
    );
}

public class AvatarOrchestrator : IAvatarOrchestrator
{
    private readonly OpenAIClient _openAiClient;
    private readonly SpeechConfig _speechConfig;
    private readonly CosmosClient _cosmosClient;
    private readonly IHubContext<AvatarHub> _hubContext;
    private readonly ILogger<AvatarOrchestrator> _logger;
    private readonly Container _sessionsContainer;

    public AvatarOrchestrator(
        OpenAIClient openAiClient,
        SpeechConfig speechConfig,
        CosmosClient cosmosClient,
        IHubContext<AvatarHub> hubContext,
        ILogger<AvatarOrchestrator> logger
    )
    {
        _openAiClient = openAiClient;
        _speechConfig = speechConfig;
        _cosmosClient = cosmosClient;
        _hubContext = hubContext;
        _logger = logger;

        // Initialize Cosmos DB container
        var database = _cosmosClient.GetDatabase("AvatarDB");
        _sessionsContainer = database.GetContainer("Sessions");
    }

    public async Task<ConversationResponse> ProcessMessageAsync(
        string sessionId,
        ConversationRequest request,
        CancellationToken cancellationToken = default
    )
    {
        try
        {
            // 1. Load or create session
            var session = await GetOrCreateSessionAsync(sessionId, request.UserId);

            // 2. Add user message to history
            session.History.Add(new Message("user", request.Message, DateTime.UtcNow));
            session.LastActivity = DateTime.UtcNow;

            // Notify clients that avatar is thinking
            await _hubContext.Clients.Group(sessionId).SendAsync(
                "AvatarStatus",
                new { status = "thinking" },
                cancellationToken
            );

            // 3. Generate AI response using Azure OpenAI
            var responseText = await GenerateResponseAsync(session, request);

            // 4. Add assistant response to history
            session.History.Add(new Message("assistant", responseText, DateTime.UtcNow));

            // 5. Generate speech with visemes
            var (audioUrl, visemes) = await GenerateSpeechAsync(
                responseText,
                request.Language ?? "en-US",
                sessionId
            );

            // 6. Save session state
            await SaveSessionAsync(session);

            // 7. Build response
            var response = new ConversationResponse(
                responseText,
                visemes,
                audioUrl,
                new Dictionary<string, object>
                {
                    ["sessionId"] = sessionId,
                    ["messageCount"] = session.History.Count,
                    ["timestamp"] = DateTime.UtcNow
                }
            );

            // 8. Broadcast to all clients in session
            await _hubContext.Clients.Group(sessionId).SendAsync(
                "AvatarResponse",
                response,
                cancellationToken
            );

            _logger.LogInformation($"Processed message for session {sessionId}");

            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error processing message for session {sessionId}");
            throw;
        }
    }

    private async Task<ConversationSession> GetOrCreateSessionAsync(
        string sessionId,
        string userId
    )
    {
        try
        {
            var response = await _sessionsContainer.ReadItemAsync<ConversationSession>(
                sessionId,
                new PartitionKey(userId)
            );
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Create new session
            var newSession = new ConversationSession
            {
                Id = sessionId,
                UserId = userId
            };

            await _sessionsContainer.CreateItemAsync(newSession, new PartitionKey(userId));
            _logger.LogInformation($"Created new session {sessionId} for user {userId}");

            return newSession;
        }
    }

    private async Task<string> GenerateResponseAsync(
        ConversationSession session,
        ConversationRequest request
    )
    {
        var messages = new List<ChatMessage>
        {
            new ChatMessage(ChatRole.System, @"
                You are Alex, a friendly AI avatar assistant.
                Keep responses under 100 words for natural speech.
                Be professional, empathetic, and helpful.
            ")
        };

        // Add conversation history (last 10 messages)
        var recentHistory = session.History.TakeLast(10);
        foreach (var msg in recentHistory)
        {
            var role = msg.Role == "user" ? ChatRole.User : ChatRole.Assistant;
            messages.Add(new ChatMessage(role, msg.Content));
        }

        var chatOptions = new ChatCompletionsOptions
        {
            Temperature = 0.7f,
            MaxTokens = 200,
            FrequencyPenalty = 0.5f,
            PresencePenalty = 0.5f
        };

        foreach (var message in messages)
        {
            chatOptions.Messages.Add(message);
        }

        var response = await _openAiClient.GetChatCompletionsAsync(
            deploymentOrModelName: "gpt-4-turbo",
            chatOptions
        );

        return response.Value.Choices[0].Message.Content;
    }

    private async Task<(string audioUrl, List<VisemeData> visemes)> GenerateSpeechAsync(
        string text,
        string language,
        string sessionId
    )
    {
        var visemes = new List<VisemeData>();

        // Configure speech synthesizer
        _speechConfig.SpeechSynthesisLanguage = language;
        _speechConfig.SpeechSynthesisVoiceName = "en-US-JennyNeural";

        // Create audio file path
        var audioFileName = $"{sessionId}_{DateTime.UtcNow.Ticks}.wav";
        var audioFilePath = Path.Combine(Path.GetTempPath(), audioFileName);

        using var audioConfig = AudioConfig.FromWavFileOutput(audioFilePath);
        using var synthesizer = new SpeechSynthesizer(_speechConfig, audioConfig);

        // Subscribe to viseme events
        synthesizer.VisemeReceived += (sender, e) =>
        {
            visemes.Add(new VisemeData(e.VisemeId, e.AudioOffset));
        };

        // Synthesize speech
        var result = await synthesizer.SpeakTextAsync(text);

        if (result.Reason == ResultReason.SynthesizingAudioCompleted)
        {
            _logger.LogInformation($"Speech synthesized: {visemes.Count} visemes");

            // Upload to Azure Blob Storage (implementation omitted)
            var audioUrl = await UploadAudioToStorageAsync(audioFilePath, audioFileName);

            // Clean up temp file
            File.Delete(audioFilePath);

            return (audioUrl, visemes);
        }
        else
        {
            throw new Exception($"Speech synthesis failed: {result.Reason}");
        }
    }

    private async Task<string> UploadAudioToStorageAsync(string filePath, string fileName)
    {
        // TODO: Implement Azure Blob Storage upload
        // For now, return placeholder URL
        return $"https://avatarstorage.blob.core.windows.net/audio/{fileName}";
    }

    private async Task SaveSessionAsync(ConversationSession session)
    {
        await _sessionsContainer.UpsertItemAsync(
            session,
            new PartitionKey(session.UserId)
        );
    }
}

// ============================================
// API CONTROLLERS
// ============================================

[ApiController]
[Route("api/avatar")]
public class AvatarController : ControllerBase
{
    private readonly IAvatarOrchestrator _orchestrator;
    private readonly ILogger<AvatarController> _logger;

    public AvatarController(
        IAvatarOrchestrator orchestrator,
        ILogger<AvatarController> logger
    )
    {
        _orchestrator = orchestrator;
        _logger = logger;
    }

    [HttpPost("conversation/{sessionId}")]
    public async Task<ActionResult<ConversationResponse>> SendMessage(
        string sessionId,
        [FromBody] ConversationRequest request,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var response = await _orchestrator.ProcessMessageAsync(
                sessionId,
                request,
                cancellationToken
            );

            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing conversation");
            return StatusCode(500, new { error = "Failed to process message" });
        }
    }

    [HttpPost("session")]
    public ActionResult<string> CreateSession([FromBody] CreateSessionRequest request)
    {
        var sessionId = Guid.NewGuid().ToString();
        _logger.LogInformation($"Created session {sessionId} for user {request.UserId}");

        return Ok(new { sessionId });
    }

    [HttpGet("health")]
    public IActionResult HealthCheck()
    {
        return Ok(new
        {
            status = "healthy",
            timestamp = DateTime.UtcNow,
            version = "1.0.0"
        });
    }
}

public record CreateSessionRequest(string UserId);

// ============================================
// PROGRAM SETUP
// ============================================

public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add services
        builder.Services.AddControllers();
        builder.Services.AddSignalR();

        // Azure OpenAI
        builder.Services.AddSingleton(sp =>
        {
            var endpoint = builder.Configuration["AzureOpenAI:Endpoint"]!;
            var apiKey = builder.Configuration["AzureOpenAI:ApiKey"]!;
            return new OpenAIClient(new Uri(endpoint), new Azure.AzureKeyCredential(apiKey));
        });

        // Azure Speech
        builder.Services.AddSingleton(sp =>
        {
            var key = builder.Configuration["AzureSpeech:Key"]!;
            var region = builder.Configuration["AzureSpeech:Region"]!;
            return SpeechConfig.FromSubscription(key, region);
        });

        // Cosmos DB
        builder.Services.AddSingleton(sp =>
        {
            var connectionString = builder.Configuration["CosmosDB:ConnectionString"]!;
            return new CosmosClient(connectionString);
        });

        // Orchestrator
        builder.Services.AddScoped<IAvatarOrchestrator, AvatarOrchestrator>();

        // CORS
        builder.Services.AddCors(options =>
        {
            options.AddDefaultPolicy(policy =>
            {
                policy.AllowAnyOrigin()
                      .AllowAnyMethod()
                      .AllowAnyHeader();
            });
        });

        var app = builder.Build();

        app.UseCors();
        app.MapControllers();
        app.MapHub<AvatarHub>("/hub/avatar");

        app.Run();
    }
}
