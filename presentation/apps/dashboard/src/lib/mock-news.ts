export interface NewsItem {
    id: string;
    title: string;
    abstract: string;
    timestamp: string; // ISO 8601 format
    sentiment: 'positive' | 'negative' | 'neutral'; // For smiley/frown face
}

/**
 * Generates mock news items
 * This will be replaced by actual API data
 * Server-side utility - can be called from both client and server
 */
export function generateMockNews(): NewsItem[] {
    const titles = [
        'Bitcoin Reaches New All-Time High',
        'Ethereum Developers Announce Major Upgrade',
        'Regulatory Clarity Expected in Q1 2025',
        'Top Crypto Exchange Reports Record Trading Volume',
        'New DeFi Protocol Launches with $50M TVL',
        'Central Banks Study CBDC Implementation',
        'Cryptocurrency Adoption Grows in Developing Nations',
        'Mining Difficulty Reaches New Peak',
        'Major Institution Adds Bitcoin to Treasury',
        'Blockchain Technology Disrupts Supply Chain',
    ];

    const abstracts = [
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
        'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
        'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
        'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
        'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.',
        'Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores.',
        'Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.',
        'Sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.',
        'Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam.',
        'At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti.',
    ];

    const sentiments: ('positive' | 'negative' | 'neutral')[] = [
        'negative',
        'positive',
        'neutral',
        'negative',
        'positive',
        'neutral',
        'positive',
        'neutral',
        'positive',
        'positive',
    ];

    const news: NewsItem[] = [];

    for (let i = 0; i < 10; i++) {
        const now = new Date();
        const minutesAgo = Math.floor(Math.random() * 1440); // Random time within last 24 hours
        const timestamp = new Date(
            now.getTime() - minutesAgo * 60000
        ).toISOString();

        news.push({
            id: `news-${i}-${Date.now()}`,
            title: titles[i],
            abstract: abstracts[i],
            timestamp,
            sentiment: sentiments[i],
        });
    }

    return news;
}
