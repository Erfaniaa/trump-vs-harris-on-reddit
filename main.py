from credentials import CLIENT_ID, CLIENT_SECRET
from config import KEYWORDS_1_LIST, KEYWORDS_2_LIST, TOP_POSTS_TIME_FILTER, MAXIMUM_POSTS_PER_SUBREDDIT, SUBREDDIT_NAMES_LIST
from data_gatherer import DataGatherer
from sentiment_analyzer import SentimentAnalyzer

if __name__ == "__main__":
	data_gatherer = DataGatherer(client_id=CLIENT_ID,
	                             client_secret=CLIENT_SECRET,
	                             subreddit_names_list=SUBREDDIT_NAMES_LIST,
								 top_posts_time_filter=TOP_POSTS_TIME_FILTER,
	                             maximum_posts_per_subreddit=MAXIMUM_POSTS_PER_SUBREDDIT)
	comments_list_by_author = data_gatherer.get_comments_list_by_author(subreddit_name="all")
	sentiment_analyzer = SentimentAnalyzer()

	keywords_1_list_total_votes = 0
	keywords_2_list_total_votes = 0

	print("Analyzing sentiment of the retrieved comments...")
	print("(if it's slow you can decrease MAXIMUM_POSTS_PER_SUBREDDIT)")

	for author_name in comments_list_by_author:
		keywords_1_list_sentiment_score = sentiment_analyzer.get_texts_list_sentiment_score(KEYWORDS_1_LIST, comments_list_by_author[author_name])
		keywords_2_list_sentiment_score = sentiment_analyzer.get_texts_list_sentiment_score(KEYWORDS_2_LIST, comments_list_by_author[author_name])
		
		if keywords_1_list_sentiment_score > keywords_2_list_sentiment_score:
			keywords_1_list_total_votes += 1
		if keywords_1_list_sentiment_score < keywords_2_list_sentiment_score:
			keywords_2_list_total_votes += 1

	print(KEYWORDS_1_LIST)
	print("Votes percent:", round(100 * keywords_1_list_total_votes / len(comments_list_by_author), 2))
	print(KEYWORDS_2_LIST)
	print("Votes percent:", round(100 * keywords_2_list_total_votes / len(comments_list_by_author), 2))

	print("Votes difference percent:", round(100 * (max(keywords_1_list_total_votes, keywords_2_list_total_votes) / min(keywords_1_list_total_votes, keywords_2_list_total_votes) - 1), 2))

	if keywords_1_list_total_votes > keywords_2_list_total_votes:
		print("May", KEYWORDS_1_LIST, "win the US 2024 election?")
	elif keywords_1_list_total_votes < keywords_2_list_total_votes:
		print("May", KEYWORDS_2_LIST, "win the US 2024 election?")
