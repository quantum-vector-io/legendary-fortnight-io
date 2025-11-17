/**
 * Copilot Studio Integration via Direct Line API
 *
 * This example shows how to connect to a Copilot Studio bot
 * and manage conversations programmatically.
 */

const axios = require('axios');
const { EventEmitter } = require('events');

class CopilotStudioClient extends EventEmitter {
  constructor(directLineSecret) {
    super();
    this.directLineSecret = directLineSecret;
    this.conversationId = null;
    this.token = null;
    this.streamUrl = null;
    this.watermark = null;
    this.pollInterval = null;
  }

  /**
   * Start a new conversation with the Copilot
   */
  async startConversation() {
    try {
      const response = await axios.post(
        'https://directline.botframework.com/v3/directline/conversations',
        {},
        {
          headers: {
            'Authorization': `Bearer ${this.directLineSecret}`,
            'Content-Type': 'application/json'
          }
        }
      );

      this.conversationId = response.data.conversationId;
      this.token = response.data.token;
      this.streamUrl = response.data.streamUrl;

      console.log(`✅ Conversation started: ${this.conversationId}`);

      // Start listening for responses
      this.startPolling();

      return this.conversationId;
    } catch (error) {
      console.error('❌ Failed to start conversation:', error.message);
      throw error;
    }
  }

  /**
   * Send a message to the Copilot
   */
  async sendMessage(text, userId = 'user-001', metadata = {}) {
    if (!this.conversationId) {
      throw new Error('No active conversation. Call startConversation() first.');
    }

    const activity = {
      type: 'message',
      from: { id: userId },
      text: text,
      channelData: metadata,
      timestamp: new Date().toISOString()
    };

    try {
      await axios.post(
        `https://directline.botframework.com/v3/directline/conversations/${this.conversationId}/activities`,
        activity,
        {
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      console.log(`📤 Sent: "${text}"`);
    } catch (error) {
      console.error('❌ Failed to send message:', error.message);
      throw error;
    }
  }

  /**
   * Poll for new messages from the Copilot
   */
  async getMessages() {
    try {
      const url = this.watermark
        ? `https://directline.botframework.com/v3/directline/conversations/${this.conversationId}/activities?watermark=${this.watermark}`
        : `https://directline.botframework.com/v3/directline/conversations/${this.conversationId}/activities`;

      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });

      this.watermark = response.data.watermark;

      // Filter for bot messages only
      const botMessages = response.data.activities.filter(
        activity => activity.from.id !== 'user-001' && activity.type === 'message'
      );

      return botMessages;
    } catch (error) {
      console.error('❌ Failed to get messages:', error.message);
      return [];
    }
  }

  /**
   * Start polling for messages
   */
  startPolling() {
    this.pollInterval = setInterval(async () => {
      const messages = await this.getMessages();

      messages.forEach(message => {
        console.log(`📥 Received: "${message.text}"`);
        this.emit('message', message);
      });
    }, 1000); // Poll every second
  }

  /**
   * Stop polling and end conversation
   */
  stopConversation() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    console.log('🛑 Conversation ended');
  }

  /**
   * Send event to trigger specific topics
   */
  async sendEvent(eventName, eventValue = {}, userId = 'user-001') {
    const activity = {
      type: 'event',
      name: eventName,
      value: eventValue,
      from: { id: userId }
    };

    await axios.post(
      `https://directline.botframework.com/v3/directline/conversations/${this.conversationId}/activities`,
      activity,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    console.log(`🎯 Event triggered: ${eventName}`);
  }
}

// ============================================
// USAGE EXAMPLE
// ============================================

async function main() {
  const client = new CopilotStudioClient('YOUR_DIRECT_LINE_SECRET');

  // Handle incoming messages
  client.on('message', (message) => {
    console.log('🤖 Copilot says:', message.text);

    // Check for suggested actions
    if (message.suggestedActions) {
      console.log('💡 Suggested actions:', message.suggestedActions.actions);
    }

    // Check for attachments (cards, images, etc.)
    if (message.attachments && message.attachments.length > 0) {
      console.log('📎 Attachments:', message.attachments);
    }
  });

  try {
    // Start conversation
    await client.startConversation();

    // Send greeting
    await client.sendMessage('Hello!', 'user-001', {
      userPreferences: {
        language: 'en-US',
        notifications: true
      }
    });

    // Wait for responses
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Ask a question
    await client.sendMessage('What can you help me with?');

    // Keep conversation alive for 10 seconds
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Trigger a specific topic via event
    await client.sendEvent('StartSupportTopic', {
      ticketId: '12345',
      priority: 'high'
    });

    // Wait and then end
    await new Promise(resolve => setTimeout(resolve, 5000));
    client.stopConversation();

  } catch (error) {
    console.error('Error:', error);
    client.stopConversation();
  }
}

// Uncomment to run
// main();

module.exports = CopilotStudioClient;
