# 🌟 AI Avatar Best Practices

Production-grade patterns and recommendations for building reliable, scalable AI avatars.

## Architecture Principles

### 1. Separation of Concerns

**DO:**
```
Frontend (UI/Avatar) ← API Gateway ← Orchestration Layer ← AI Services
```

**DON'T:**
```
Frontend → Directly call OpenAI/Speech APIs
```

**Why**: Centralized control, security, cost management, easier updates

### 2. Fail Gracefully

```typescript
// Good: Fallback chain
async function getResponse(message: string): Promise<string> {
  try {
    // Try Copilot Studio first
    return await copilotStudio.ask(message);
  } catch (error) {
    try {
      // Fallback to Azure OpenAI
      return await azureOpenAI.chat(message);
    } catch (error) {
      // Final fallback to static response
      return "I'm experiencing technical difficulties. Please try again.";
    }
  }
}
```

### 3. Stateless Services

- Store session state externally (Cosmos DB, Redis)
- Enable horizontal scaling
- Facilitate load balancing
- Support multi-region deployments

---

## Conversation Design

### Keep Responses Concise

**Good:**
> "Your order #12345 will arrive Thursday, Nov 21st. Track it at tracking.example.com/12345"

**Bad:**
> "Thank you so much for your patience! I've looked up your order and I'm excited to tell you that order number 12345 is currently in transit and based on our shipping estimates, it should arrive at your doorstep on Thursday, November 21st, 2025. You can track its progress in real-time by visiting our tracking portal at..."

**Why**: Natural speech should be brief. Long responses feel unnatural and bore users.

### Use Conversational Language

**Good:**
> "I can help with that! What's your order number?"

**Bad:**
> "REQUEST ACKNOWLEDGED. PLEASE PROVIDE ORDER IDENTIFICATION NUMBER FOR QUERY PROCESSING."

### Ask One Question at a Time

**Good:**
> "What's your email address?"
> (wait for response)
> "Thanks! And your order number?"

**Bad:**
> "What's your email address, order number, and preferred callback time?"

---

## Performance Optimization

### 1. Response Streaming

```python
# Stream OpenAI responses for faster perceived performance
async for chunk in openai_client.stream_response(user_message):
    # Send immediately to TTS
    await tts_service.synthesize(chunk)
    # Send to frontend
    await signalr.send("TextChunk", chunk)
```

**Benefit**: User sees/hears avatar responding immediately instead of waiting for complete response.

### 2. Parallel Processing

```typescript
// Bad: Sequential (slow)
const aiResponse = await getAIResponse(message);
const speech = await textToSpeech(aiResponse);
const visemes = extractVisemes(speech);

// Good: Parallel where possible
const [aiResponse, userContext] = await Promise.all([
  getAIResponse(message),
  getUserContext(userId)
]);
```

### 3. Smart Caching

```typescript
// Cache common responses
const CACHE_TTL = 3600; // 1 hour

async function getCachedResponse(query: string): Promise<string> {
  const cacheKey = `response:${hash(query)}`;

  // Check cache first
  let response = await redis.get(cacheKey);

  if (!response) {
    // Generate and cache
    response = await generateResponse(query);
    await redis.setex(cacheKey, CACHE_TTL, response);
  }

  return response;
}
```

**Cache candidates:**
- FAQ responses
- Product information
- Business hours
- Common greetings

### 4. Token Optimization

```python
# Limit conversation history
MAX_HISTORY = 10

def prepare_messages(session):
    messages = [system_prompt]

    # Keep only recent messages
    recent = session.history[-MAX_HISTORY:]

    # Summarize older context if needed
    if len(session.history) > MAX_HISTORY:
        summary = summarize_conversation(session.history[:-MAX_HISTORY])
        messages.append({"role": "system", "content": f"Previous context: {summary}"})

    messages.extend(recent)
    return messages
```

---

## Security Best Practices

### 1. Never Expose Secrets

```yaml
# ❌ BAD
const openai = new OpenAI({
  apiKey: "sk-abc123..."  # Hardcoded!
});

# ✅ GOOD
const openai = new OpenAI({
  apiKey: process.env.AZURE_OPENAI_KEY  # From environment
});
```

### 2. Input Validation

```csharp
// Validate and sanitize all user input
public class ConversationRequest
{
    [Required]
    [StringLength(1000, MinimumLength = 1)]
    public string Message { get; set; }

    [RegularExpression(@"^[a-zA-Z0-9-]+$")]
    public string UserId { get; set; }
}
```

### 3. Rate Limiting

```typescript
// Prevent abuse
const rateLimiter = new RateLimiter({
  windowMs: 60000, // 1 minute
  max: 20, // 20 requests per minute per user
  message: "Too many requests. Please slow down."
});

app.use('/api/avatar', rateLimiter);
```

### 4. Content Moderation

```python
# Check for inappropriate content
def is_safe_content(text: string) -> bool:
    # Use Azure Content Safety
    result = content_safety_client.analyze_text(text)

    return (
        result.hate_score < 0.5 and
        result.sexual_score < 0.5 and
        result.violence_score < 0.5 and
        result.self_harm_score < 0.5
    )

# In your conversation handler
if not is_safe_content(user_message):
    return "I'm not able to respond to that type of content."
```

### 5. Data Privacy

```typescript
// PII detection and masking
function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "***-**-****")  // SSN
    .replace(/\b\d{16}\b/g, "****-****-****-****")      // Credit card
    .replace(/\b[\w.-]+@[\w.-]+\.\w+\b/g, "***@***.***"); // Email
}

// Log masked version only
logger.info(`User message: ${maskPII(userMessage)}`);
```

---

## Cost Management

### 1. Choose Right Model for Task

```python
# Simple queries: Use GPT-3.5 Turbo (cheaper)
def route_to_model(query: str) -> str:
    complexity = assess_complexity(query)

    if complexity == "simple":
        return "gpt-35-turbo"  # $0.0015/1K tokens
    else:
        return "gpt-4-turbo"    # $0.01/1K tokens

# Examples of simple queries:
# - "What are your hours?"
# - "Hello"
# - "Thanks"
```

### 2. Set Token Limits

```javascript
const response = await openai.chat.completions.create({
  model: "gpt-4-turbo",
  messages: messages,
  max_tokens: 150,  // Enforce reasonable limit
  temperature: 0.7
});
```

### 3. Monitor Usage

```sql
-- Query Application Insights
customEvents
| where name == "OpenAI_Request"
| extend tokens = toint(customDimensions.tokens_used)
| extend model = tostring(customDimensions.model)
| summarize
    TotalTokens = sum(tokens),
    AvgTokens = avg(tokens),
    RequestCount = count()
    by model, bin(timestamp, 1d)
| extend EstimatedCost =
    case(
      model == "gpt-4-turbo", TotalTokens * 0.00001,
      model == "gpt-35-turbo", TotalTokens * 0.0000015,
      0
    )
```

### 4. Implement Quotas

```csharp
// Per-user daily limits
public async Task<bool> CheckUserQuota(string userId)
{
    var today = DateTime.UtcNow.Date;
    var key = $"quota:{userId}:{today:yyyy-MM-dd}";

    var currentUsage = await redis.GetAsync<int>(key);

    if (currentUsage >= MAX_REQUESTS_PER_DAY)
    {
        return false; // Quota exceeded
    }

    await redis.IncrementAsync(key);
    await redis.ExpireAsync(key, TimeSpan.FromDays(1));

    return true;
}
```

---

## Avatar UX Best Practices

### 1. Visual Feedback States

```typescript
enum AvatarState {
  Idle = "idle",           // Waiting for user
  Listening = "listening", // STT active
  Thinking = "thinking",   // Processing response
  Speaking = "speaking",   // TTS playing
  Error = "error"          // Something went wrong
}

// Update avatar visual cues
function setAvatarState(state: AvatarState) {
  switch(state) {
    case AvatarState.Listening:
      avatar.playAnimation("listening");
      showIndicator("🎤 Listening...");
      break;
    case AvatarState.Thinking:
      avatar.playAnimation("thinking");
      showIndicator("💭 Thinking...");
      break;
    // ...
  }
}
```

### 2. Natural Timing

```typescript
// Add natural pauses
async function speakWithPauses(text: string) {
  const sentences = text.split(/[.!?]+/);

  for (const sentence of sentences) {
    await tts.speak(sentence);

    // Brief pause between sentences
    await sleep(300);
  }
}
```

### 3. Non-verbal Communication

```python
# Map sentiment to expressions
def get_expression(text: str) -> str:
    sentiment = analyze_sentiment(text)

    if sentiment > 0.6:
        return "happy"
    elif sentiment < -0.3:
        return "concerned"
    else:
        return "neutral"

# Apply to avatar
response_text = "I'm sorry to hear that."
expression = get_expression(response_text)  # "concerned"
avatar.set_expression(expression)
```

### 4. Progressive Disclosure

```typescript
// Don't overwhelm with options
// Good: Show 3-4 options at a time

const primaryOptions = [
  "Check order status",
  "Product information",
  "Speak to agent"
];

const moreOptions = [
  "Return policy",
  "Account settings",
  "Feedback"
];

// Show primary first
showQuickReplies(primaryOptions);
// "More options..." button reveals moreOptions
```

---

## Error Handling

### 1. User-Friendly Messages

```typescript
// Bad
throw new Error("OpenAI API returned 429");

// Good
try {
  const response = await callOpenAI();
} catch (error) {
  if (error.status === 429) {
    return "I'm handling a lot of conversations right now. Could you try again in a moment?";
  } else if (error.status === 503) {
    return "I'm experiencing technical difficulties. Let me transfer you to a human agent.";
  } else {
    return "Something went wrong on my end. Could you rephrase that?";
  }
}
```

### 2. Automatic Retry with Backoff

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_azure_service(request):
    """Automatically retry with exponential backoff"""
    return await azure_client.call(request)
```

### 3. Circuit Breaker Pattern

```csharp
// Prevent cascading failures
public class CircuitBreaker
{
    private int _failureCount = 0;
    private DateTime _lastFailureTime;
    private bool _isOpen = false;

    private const int THRESHOLD = 5;
    private const int TIMEOUT_SECONDS = 60;

    public async Task<T> ExecuteAsync<T>(Func<Task<T>> action)
    {
        if (_isOpen)
        {
            if ((DateTime.UtcNow - _lastFailureTime).TotalSeconds > TIMEOUT_SECONDS)
            {
                _isOpen = false; // Try again
                _failureCount = 0;
            }
            else
            {
                throw new Exception("Circuit breaker is open");
            }
        }

        try
        {
            var result = await action();
            _failureCount = 0; // Reset on success
            return result;
        }
        catch
        {
            _failureCount++;
            _lastFailureTime = DateTime.UtcNow;

            if (_failureCount >= THRESHOLD)
            {
                _isOpen = true;
            }

            throw;
        }
    }
}
```

---

## Accessibility

### 1. Keyboard Navigation

```html
<!-- Ensure all controls are keyboard accessible -->
<button class="avatar-control"
        tabindex="0"
        aria-label="Start conversation">
  Talk to avatar
</button>
```

### 2. Screen Reader Support

```html
<!-- Announce avatar state changes -->
<div role="status" aria-live="polite" aria-atomic="true">
  <span class="sr-only" id="avatar-status">
    Avatar is thinking
  </span>
</div>
```

### 3. Captions/Transcripts

```typescript
// Always show text alongside speech
function displayCaptions(text: string, speaker: string) {
  const caption = document.createElement('div');
  caption.className = 'caption';
  caption.innerHTML = `<strong>${speaker}:</strong> ${text}`;
  captionContainer.appendChild(caption);

  // Auto-scroll
  captionContainer.scrollTop = captionContainer.scrollHeight;
}
```

### 4. High Contrast Mode

```css
/* Support high contrast themes */
@media (prefers-contrast: high) {
  .avatar-container {
    border: 2px solid currentColor;
  }

  .caption-text {
    background: Canvas;
    color: CanvasText;
  }
}
```

---

## Testing Strategies

### 1. Unit Tests

```typescript
describe('AvatarOrchestrator', () => {
  it('should generate response within 2 seconds', async () => {
    const start = Date.now();
    const response = await orchestrator.processMessage(
      'session-123',
      { userId: 'user-1', message: 'Hello' }
    );
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(2000);
    expect(response.responseText).toBeDefined();
  });

  it('should handle errors gracefully', async () => {
    // Mock OpenAI failure
    mockOpenAI.chat.mockRejectedValue(new Error('API Error'));

    const response = await orchestrator.processMessage(
      'session-123',
      { userId: 'user-1', message: 'Hello' }
    );

    expect(response.responseText).toContain('technical difficulties');
  });
});
```

### 2. Integration Tests

```python
def test_end_to_end_conversation():
    """Test complete conversation flow"""
    # Start session
    session_id = api.create_session(user_id="test-user")

    # Send message
    response = api.send_message(session_id, "What are your hours?")

    # Verify response
    assert response.status_code == 200
    assert "hours" in response.json()["responseText"].lower()
    assert len(response.json()["visemes"]) > 0
    assert response.json()["audioUrl"].startswith("https://")
```

### 3. Load Tests

```javascript
// k6 load test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100
    { duration: '2m', target: 200 },  // Ramp to 200
    { duration: '5m', target: 200 },  // Stay at 200
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% under 2s
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function() {
  const response = http.post(
    'https://api.example.com/avatar/conversation/test-session',
    JSON.stringify({
      userId: 'load-test-user',
      message: 'Hello, how are you?'
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });

  sleep(1);
}
```

---

## Monitoring & Observability

### Key Metrics to Track

```typescript
// Custom telemetry
telemetry.trackMetric("ConversationDuration", durationMs);
telemetry.trackMetric("TokensUsed", tokensUsed);
telemetry.trackMetric("SpeechLatency", speechLatencyMs);

telemetry.trackEvent("ConversationCompleted", {
  userId: userId,
  messageCount: messageCount,
  sentiment: overallSentiment,
  escalated: wasEscalated.toString()
});
```

### Dashboard Queries

```kusto
// Average tokens per conversation
customEvents
| where name == "ConversationCompleted"
| extend tokens = toint(customDimensions.totalTokens)
| summarize avg(tokens) by bin(timestamp, 1h)

// P95 response time
requests
| where url contains "/avatar/conversation"
| summarize percentile(duration, 95) by bin(timestamp, 5m)

// User satisfaction
customEvents
| where name == "FeedbackReceived"
| extend rating = toint(customDimensions.rating)
| summarize
    AvgRating = avg(rating),
    Count = count()
    by bin(timestamp, 1d)
```

---

## Documentation Standards

### 1. API Documentation

Use OpenAPI/Swagger:

```yaml
openapi: 3.0.0
info:
  title: AI Avatar API
  version: 1.0.0
paths:
  /api/avatar/conversation/{sessionId}:
    post:
      summary: Send message to avatar
      parameters:
        - name: sessionId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ConversationRequest'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConversationResponse'
```

### 2. Code Comments

```python
def process_conversation(
    session_id: str,
    user_message: str,
    context: Dict[str, Any] = None
) -> ConversationResponse:
    """
    Process a user message and generate avatar response.

    This function orchestrates the complete conversation flow:
    1. Load session state from Cosmos DB
    2. Generate AI response using Azure OpenAI
    3. Synthesize speech with visemes
    4. Save updated session state
    5. Broadcast to connected clients via SignalR

    Args:
        session_id: Unique session identifier
        user_message: The user's input text
        context: Optional additional context (customer data, etc.)

    Returns:
        ConversationResponse with text, audio URL, and visemes

    Raises:
        SessionNotFoundError: If session_id doesn't exist
        AIServiceError: If OpenAI or Speech services fail

    Example:
        >>> response = process_conversation(
        ...     "session-123",
        ...     "What are your hours?",
        ...     {"customer_tier": "premium"}
        ... )
        >>> print(response.text)
        "We're open Monday-Friday, 9 AM to 5 PM."
    """
```

---

**Remember**: These practices aren't rules—adapt them to your specific needs!

---

**Last Updated**: 2025-11-17
