# https://picture.learntosolveit.com

## Understand the Picture of the Day

A browser extension and web application that displays beautiful pictures from
NASA APOD, Wikipedia POD, and Bing POD on every new tab, with AI-enhanced
descriptions featuring simplified explanations and interactive Wikipedia links.


**Development and Testing**

This is a python django app. `backend` directory is django app, and `extension` provides the browser extension code.The project includes comprehensive tests for management commands. To run the tests:

Make sure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

Run all tests
```bash
python manage.py test
```

**frontend tests**

```bash
cd tests
npm install
npm test
```


**Local Testing**

```bash
# Add  NASA_API_KEY and OPENAI_API_KEY to your .env

cp .env.example .env
```

```bash
# Start the Django server
python manage.py runserver
```

Visit `http://localhost:8000/`


**Deployment**

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick deployment workflow:
1. Deploy website/API to Kubernetes
2. Test website and API endpoints
3. Package browser extension
4. Test browser extension
5. Publish to extension stores

**Credits**

- Images from NASA's Astronomy Picture of the Day
- Wikipedia Picture of the Day
- Bing Picture of the Day

**Copyright**

Senthil Kumaran <orsenthil@gmail.com>