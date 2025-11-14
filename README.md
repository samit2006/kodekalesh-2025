<img width="704" height="627" alt="image" src="https://github.com/user-attachments/assets/538ecad8-ee05-4926-b729-4458c4bea78f" /># kodekalesh-2025



#Our Problem Statement
Public health agencies are often reactive. By the time a disease outbreak (like influenza, dengue fever, or a novel virus) is officially confirmed, it has already begun to spread. This "lag time" costs crucial days, allowing the disease to take hold. An early warning system could allow authorities to mobilize resources, launch public awareness campaigns, and implement preventative measures before the outbreak becomes critical.


Our Solution
Project Sentinel   (Early outbreak warning)


Our Solution

Project Sentinel is a dashboard that provides this early warning. A health official can select a disease and a region to instantly see:

A "Threat Score" (1-10): A composite score of digital signals.

A "Threat Level" (Low, Guarded, Elevated, High): A clear, color-coded warning.

AI-Generated Recommendation: A 1-2 sentence action plan written by an AI public health analyst (powered by Amazon Bedrock).

Data Visualizations: A chart of (simulated) Google search trends.


 Tech Stack

Frontend: HTML5, Tailwind CSS, Chart.js (a single, simple index.html file)

Backend: AWS Lambda (Python 3.12)

API: AWS API Gateway (HTTP API)

Generative AI: Amazon Bedrock (using the Anthropic Claude 3 Haiku model)
Application Architecture
[Frontend (HTML/JS/Chart.js)] → [AWS API Gateway] → [AWS Lambda] → [Amazon Bedrock (Claude 3 Haiku)]
(User Interface) → (HTTP Trigger) → (Business Logic) → (AI Analysis)

A health official opens index.html and selects a disease, city, and region.

The browser sends a GET request to our API Gateway endpoint.

The API Gateway triggers our AWS Lambda function.

The Lambda function (Python) generates mock data (see note below) to simulate Google Trends and social media spikes.

It calculates a "Threat Score" from this mock data.

This score and context are sent in a prompt to Amazon Bedrock.

The Claude 3 Haiku AI model analyzes the prompt and returns a 1-2 sentence "Recommended Action" (e.g., "ALERT: Elevated search interest. Recommend alerting clinics and launching a preventative awareness campaign.").

The Lambda function returns all this information (score, level, AI action, chart data) as a JSON object.

The frontend receives the JSON and dynamically updates the dashboard.



A Note on Mock Data: A Strategic Pivot

Our initial plan was to use live data from Google Trends (pytrends). During the hackathon, we ran into Google's Error 429 (Too Many Requests) rate-limiting, which is a common and unavoidable roadblock for automated scraping.

We made a strategic decision: instead of losing hours trying to bypass this, we would focus on the more innovative and complex part of the stack.

We chose to mock the input data (the trends and social scores) in order to build a fully functional, end-to-end serverless pipeline that integrates a Generative AI model for real-time analysis. This demonstrates our ability to build a robust, AI-powered system, which was a better use of our limited time.


Future Work

Integrate Real Data: Use a Lambda Layer to package pytrends and run it on a 1-hour cron job to cache results in S3, avoiding rate-limits.

Real Social Media: Integrate the X (Twitter) and Reddit APIs for social chatter analysis.

More Data Sources: Add weather data (for mosquito-borne illness) and flight data (for spread prediction).

Anomaly Detection: Use a simple ML model (like Isolation Forest) to auto-detect spikes instead of manual calculation.
