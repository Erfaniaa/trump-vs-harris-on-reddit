from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob


class SentimentAnalyzer:

	EPSILON = 10 ** -2

	def __init__(self):
		pass

	@staticmethod
	def get_single_text_sentiment_score(words_list: list[str], text: str) -> int:
		text_contains_word = False

		for word in words_list:
			if word.lower() in text.lower():
				text_contains_word = True
				break

		if not text_contains_word:
			return 0
		
		total_sentiment_score = 0

		vader_analyzer = SentimentIntensityAnalyzer()
		vader_sentiment = vader_analyzer.polarity_scores(text)

		textblob = TextBlob(text)
		textblob_polarity = textblob.sentiment.polarity

		if vader_sentiment["compound"] > SentimentAnalyzer.EPSILON:
			vader_score = 1
		elif vader_sentiment["compound"] < -SentimentAnalyzer.EPSILON:
			vader_score = -1
		else:
			vader_score = 0

		if textblob_polarity > SentimentAnalyzer.EPSILON:
			textblob_score = 1
		elif textblob_polarity < -SentimentAnalyzer.EPSILON:
			textblob_score = -1
		else:
			textblob_score = 0

		total_sentiment_score = vader_score + textblob_score

		total_sentiment_score = min(total_sentiment_score, 1)
		total_sentiment_score = max(total_sentiment_score, -1)

		return total_sentiment_score
	
	@staticmethod
	def get_texts_list_sentiment_score(words_list: list[str], texts_list: list[str]) -> int:
		total_sentiment_score = 0

		for text in texts_list:
			total_sentiment_score += SentimentAnalyzer.get_single_text_sentiment_score(words_list, text)

		if total_sentiment_score >= 1:
			return 1
		elif total_sentiment_score <= -1:
			return -1
		else:
			return 0
