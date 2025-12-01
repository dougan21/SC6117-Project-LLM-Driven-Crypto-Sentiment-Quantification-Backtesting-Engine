import { ChatMessage } from '@/hooks/use-chatbot';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { message, history } = body;

        if (!message || typeof message !== 'string') {
            return Response.json(
                { error: 'Message is required' },
                { status: 400 }
            );
        }

        // TODO: Integrate with actual LLM API (OpenAI, Anthropic, etc.)
        // This is a mock response for development
        const mockResponse = generateMockChatResponse(
            message,
            history as ChatMessage[]
        );

        return Response.json(
            {
                message: mockResponse,
                timestamp: new Date().toISOString(),
            },
            {
                status: 200,
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );
    } catch (error) {
        console.error('Error processing chat message:', error);
        return Response.json(
            { error: 'Failed to process message' },
            { status: 500 }
        );
    }
}

/**
 * Generates mock chatbot responses based on message content
 * This will be replaced with actual LLM integration
 */
function generateMockChatResponse(
    message: string,
    history: ChatMessage[]
): string {
    const lowerMessage = message.toLowerCase();

    // Pattern matching for common queries
    if (lowerMessage.includes('bitcoin') || lowerMessage.includes('btc')) {
        return 'Bitcoin is currently showing strong momentum. Based on recent data, the price has been fluctuating between $40,000 and $45,000. Would you like me to analyze specific trends?';
    }

    if (lowerMessage.includes('ethereum') || lowerMessage.includes('eth')) {
        return 'Ethereum has been performing well recently. The network upgrade has positively impacted sentiment. Current price range is around $2,000-$2,300.';
    }

    if (lowerMessage.includes('predict') || lowerMessage.includes('forecast')) {
        return 'Our ML models analyze multiple factors including historical prices, sentiment analysis, and market trends. The predictions are updated in real-time on the dashboard chart.';
    }

    if (lowerMessage.includes('sentiment') || lowerMessage.includes('news')) {
        return 'News sentiment analysis shows mixed signals. Recent positive news includes institutional adoption, while regulatory concerns remain. Check the news feed for detailed sentiment indicators.';
    }

    if (
        lowerMessage.includes('help') ||
        lowerMessage.includes('what can you')
    ) {
        return 'I can help you with:\n• Cryptocurrency price analysis\n• Market trend predictions\n• News sentiment interpretation\n• Technical indicators explanation\n\nJust ask me anything about crypto markets!';
    }

    if (lowerMessage.includes('thank') || lowerMessage.includes('thanks')) {
        return "You're welcome! Feel free to ask if you have more questions about cryptocurrency markets.";
    }

    // Default response
    return "I'm here to help with cryptocurrency analysis. This feature is still being developed with full LLM integration. In the meantime, try asking about Bitcoin, Ethereum, predictions, or market sentiment!";
}
