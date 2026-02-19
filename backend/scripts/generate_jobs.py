
import json
import uuid
import random
from datetime import datetime, timedelta

# Original 10 jobs
original_jobs = [
  {
    "title": "Senior Backend Engineer (Python/FastAPI)",
    "company": "Careem",
    "location": "Dubai, UAE",
    "description": "About the Role:\nCareem is looking for a Senior Backend Engineer to join our Super App team. You will be responsible for building high-scale microservices that power millions of rides and orders daily.\n\nKey Responsibilities:\n- Design and implement scalable RESTful APIs using Python (FastAPI/Django).\n- Optimize database performance (PostgreSQL, Redis).\n- Work with asynchronous task queues (Celery/RabbitMQ).\n- Collaborate with mobile and frontend teams.\n- Ensure high availability and reliability of services.\n\nRequirements:\n- 5+ years of experience in backend development.\n- Expert in Python, FastAPI, and SQL.\n- Experience with Docker, Kubernetes, and AWS.\n- Strong understanding of distributed systems and microservices.\n- Experience with Event-Driven Architecture (Kafka) is a plus.",
    "salary": "AED 25,000 - 35,000 / Month",
    "posted_at": "2026-02-18T09:00:00",
    "source": "LinkedIn"
  },
  {
    "title": "Full Stack Developer (React + Node.js)",
    "company": "Talabat",
    "location": "Dubai, UAE",
    "description": "Join Talabat, the leading food delivery platform in the MENA region. We are scaling our tech team and looking for a Full Stack Developer to build delightful user experiences.\n\nWhat you will do:\n- Develop responsive web applications using React.js, TypeScript, and Tailwind CSS.\n- Build robust backend services with Node.js and Express.\n- Integrate with third-party APIs (Maps, Payments).\n- Write clean, testable code (Jest, Cypress).\n\nWhat we look for:\n- 3+ years of full stack experience.\n- Proficiency in JavaScript/TypeScript, React, and Node.js.\n- Experience with MongoDB and PostgreSQL.\n- Familiarity with CI/CD pipelines (GitHub Actions).\n- Passion for UI/UX and performance optimization.",
    "salary": "AED 18,000 - 25,000 / Month",
    "posted_at": "2026-02-17T14:30:00",
    "source": "Indeed"
  },
  {
    "title": "DevOps Engineer",
    "company": "Emirates Group",
    "location": "Dubai, UAE",
    "description": "Emirates Group IT is seeking a skilled DevOps Engineer to manage our cloud infrastructure and deployment pipelines.\n\nResponsibilities:\n- Manage AWS infrastructure using Terraform (IaC).\n- Automate deployment workflows using Jenkins and GitLab CI.\n- Monitor system health using Prometheus, Grafana, and ELK Stack.\n- Ensure security best practices in cloud environments.\n- Manage Kubernetes clusters (EKS).\n\nQualifications:\n- 4+ years of DevOps/SRE experience.\n- Strong AWS knowledge (EC2, S3, RDS, Lambda, VPC).\n- Proficiency in Linux scripting (Bash/Python).\n- Hands-on experience with Docker and Kubernetes.\n- Certified AWS Solutions Architect is preferred.",
    "salary": "AED 22,000 - 30,000 / Month",
    "posted_at": "2026-02-16T11:15:00",
    "source": "NaukriGulf"
  },
  {
    "title": "AI/ML Engineer",
    "company": "G42",
    "location": "Abu Dhabi, UAE",
    "description": "G42 is at the forefront of AI innovation. We are looking for an AI Engineer to build Large Language Model (LLM) applications.\n\nRole:\n- Fine-tune and deploy LLMs (Llama 3, Mistral) for enterprise use cases.\n- Build RAG (Retrieval Augmented Generation) pipelines using LangChain and Vector Databases (Pinecone/Milvus).\n- Optimize model inference latency.\n- Work with data scientists to productize ML models.\n\nStack:\n- Python, PyTorch, TensorFlow.\n- HuggingFace Transformers, LangChain.\n- Docker, FastAPI for model serving.\n- Cloud: Azure / AWS.\n\nRequirements:\n- Masters in CS/AI or equivalent experience.\n- 3+ years in Machine Learning engineering.\n- Experience with NLP and Generative AI.",
    "salary": "AED 30,000 - 45,000 / Month",
    "posted_at": "2026-02-19T08:45:00",
    "source": "LinkedIn"
  },
  {
    "title": "Senior Frontend Engineer",
    "company": "Noon",
    "location": "Dubai, UAE",
    "description": "Noon is the Middle East's homegrown online marketplace. We are looking for a Senior Frontend Engineer to lead our consumer-facing web team.\n\nResponsibilities:\n- Architect and build scalable frontend applications using Next.js.\n- Optimize Core Web Vitals and SEO performance.\n- Mentor junior developers and conduct code reviews.\n- Collaborate with designers on the Design System.\n\nTech Stack:\n- React, Next.js, Redux/Zustand.\n- SCSS / Tailwind / Styled Components.\n- Webpack / Vite.\n\nRequirements:\n- 5+ years of frontend development.\n- Deep understanding of DOM, CSS, and JS runtime.\n- Experience with high-traffic e-commerce sites.",
    "salary": "AED 28,000 - 38,000 / Month",
    "posted_at": "2026-02-15T10:00:00",
    "source": "LinkedIn"
  },
  {
    "title": "Product Manager - Fintech",
    "company": "Tabby",
    "location": "Dubai, UAE",
    "description": "Tabby is revolutionizing shopping in MENA. We need a Product Manager to drive our 'Shop Now Pay Later' product.\n\nRole:\n- Define product roadmap and strategy.\n- Work with engineering and design to deliver features.\n- Analyze user data to make informed decisions.\n- Manage stakeholder expectations.\n\nRequirements:\n- 4+ years of Product Management experience in Fintech.\n- Strong analytical skills (SQL, Amplitude).\n- Experience with Agile/Scrum.\n- Excellent communication skills.",
    "salary": "AED 25,000 - 35,000 / Month",
    "posted_at": "2026-02-18T16:20:00",
    "source": "Indeed"
  },
  {
    "title": "Cyber Security Analyst",
    "company": "DarkMatter",
    "location": "Abu Dhabi, UAE",
    "description": "Protect critical infrastructure from cyber threats. Monitor SOC alerts, conduct vulnerability assessments, and respond to incidents.\n\nSkills:\n- SIEM (Splunk, QRadar).\n- Network Security (Firewalls, IDS/IPS).\n- Penetration Testing tools (Metasploit, Burp Suite).\n- Incident Response frameworks (NIST).\n\nCertifications:\n- CISSP, CEH, or OSCP preferred.",
    "salary": "AED 20,000 - 28,000 / Month",
    "posted_at": "2026-02-14T09:30:00",
    "source": "NaukriGulf"
  },
  {
    "title": "Senior Data Engineer",
    "company": "Kitopi",
    "location": "Dubai, UAE",
    "description": "Kitopi is the world's leading cloud kitchen platform. We handle massive amounts of food order data.\n\nRole:\n- Build scalable data pipelines (ETL/ELT) using Airflow and dbt.\n- Manage Data Warehouse (Snowflake / BigQuery).\n- Implement real-time data streaming with Kafka.\n- Ensure data quality and governance.\n\nTech:\n- Python, SQL (Advanced).\n- Spark, Kafka, Airflow.\n- AWS/GCP data services.",
    "salary": "AED 27,000 - 37,000 / Month",
    "posted_at": "2026-02-17T11:00:00",
    "source": "LinkedIn"
  },
    {
    "title": "Python Developer",
    "company": "Dubizzle",
    "location": "Dubai, UAE",
    "description": "Dubizzle is the leading classifieds platform. We are rewriting our core services in Python.\n\nRole:\n- Rewrite legacy PHP monoliths into Python Microservices.\n- Maintain high code quality and test coverage.\n- Work with PostgreSQL and Elasticsearch.\n\nRequirements:\n- 3+ years in Python (Django/Flask/FastAPI).\n- Experience with REST APIs and GraphQL.\n- Familiarity with search engines (Elasticsearch/Solr).",
    "salary": "AED 18,000 - 26,000 / Month",
    "posted_at": "2026-02-18T13:45:00",
    "source": "Indeed"
  },
  {
    "title": "Staff Software Engineer",
    "company": "PropertyFinder",
    "location": "Dubai, UAE",
    "description": "Lead the technical direction for PropertyFinder's search experience.\n\nRole:\n- Design high-availability systems.\n- Solve complex distributed system problems.\n- Mentor senior engineers.\n- Drive technical strategy.\n\nRequirements:\n- 10+ years of software engineering.\n- Proven track record of designing systems at scale.\n- Polyglot (Go, Python, PHP, or Java).\n- Deep database knowledge.",
    "salary": "AED 45,000 - 60,000 / Month",
    "posted_at": "2026-02-12T10:00:00",
    "source": "LinkedIn"
  }
]

# Generate 50 jobs by mixing and matching
companies = ["Careem", "Talabat", "Noon", "Emirates Group", "Tabby", "G42", "Kitopi", "PropertyFinder", "Dubizzle", "DarkMatter", "Etisalat", "Du", "Mubadala", "ADNOC"]
roles = ["Backend", "Frontend", "Full Stack", "DevOps", "Data", "AI/ML", "Product", "Security"]
levels = ["Junior", "Mid-Level", "Senior", "Lead", "Staff", "Principal"]

new_jobs = []
for i in range(50):
    base_job = original_jobs[i % len(original_jobs)]
    
    # Modify
    comp = companies[i % len(companies)]
    role_type = roles[i % len(roles)]
    level = levels[i % len(levels)]
    
    title = f"{level} {role_type} Engineer"
    if role_type == "Product": title = f"{level} Product Manager"
    
    new_job_copy = base_job.copy()
    new_job_copy["title"] = title
    new_job_copy["company"] = comp
    new_job_copy["external_id"] = str(uuid.uuid4())
    new_job_copy["posted_at"] = (datetime.now() - timedelta(hours=i*2)).isoformat()
    new_job_copy["description"] = base_job["description"].replace(base_job["company"], comp)
    
    new_jobs.append(new_job_copy)

# Save
with open("app/services/scraper/data/dubai_tech_jobs.json", "w") as f:
    json.dump(new_jobs, f, indent=2)

print(f"Generated {len(new_jobs)} jobs.")
