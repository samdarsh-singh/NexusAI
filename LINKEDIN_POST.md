🚀 **Just Built: High-Scale Job Aggregation & ATS Engine**

I’ve recently architected and built a production-ready backend system designed to solve a common recruitment tech challenge: aggregating thousands of jobs and intelligently scoring resumes against them at scale.

**Key Engineering Highlights:**
*   **Hybrid Database Architecture**: leveraged **PostgreSQL** for structured relational data (jobs, scores) and **MongoDB** as a raw data lake for scraped content, ensuring full data lineage and auditability.
*   **Async-First Design**: Built with **FastAPI** and **Celery**, offloading heavy scraping and NLP scoring tasks to background workers to maintain <50ms API response times.
*   **Smart ATS Scoring**: Implemented a hybrid scoring engine. It doesn't just count keywords—it uses **Spacy** for entity extraction and **OpenAI embeddings** to understand semantic relevance (e.g., knowing that "React" implies "Frontend").
*   **Scalable Ingestion**: Designed a modular scraper interface with robust deduplication logic using content hashing, preventing data noise from overlapping job posts.

**Tech Stack:** Python, FastAPI, PostgreSQL, MongoDB, Docker, Celery, Redis.

Check out the architecture details below! 👇

#BackendEngineering #Python #FastAPI #SystemDesign #DataEngineering #CloudNative
