# Trump vs. Harris Based on Reddit Comments
Analyze Reddit comments using NLP to predict the potential winner of the US 2024 election

<img src="https://github.com/user-attachments/assets/da68bd0a-12d9-4e43-ab37-9445f28642e3" width="500">

## Description

This GitHub repository contains a project that leverages Python to retrieve and analyze political comments from Reddit. The project is structured into two primary components: data retrieval and sentiment analysis. Using the PRAW library, the project efficiently pulls comments from political discussions on Reddit. These comments are then processed through NLP algorithms—specifically vaderSentiment and TextBlob—to predict whether the commenters are likely to support Donald Trump or Kamala Harris. Currently, the NLP analysis component requires further development and refinement. Contributions aimed at enhancing the NLP techniques or improving the overall accuracy of sentiment predictions are highly encouraged and appreciated.

## Usage
1. Clone the repository.
2. Run `pip3 install -r requirements.txt`.
3. Get your credentials from [Reddit](https://www.reddit.com/prefs/apps) and add them to `credentials.py`.
4. Edit `config.py`.
5. Run `python3 main.py`.

