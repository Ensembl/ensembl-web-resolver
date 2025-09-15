# Ensembl Web Resolver
The resolver service generates new Ensembl website urls for different features based on their stable ids, as well as other optional parameters.
### Deploy the app and run docker-compose:
 
 `$ git clone https://github.com/Ensembl/ensembl-web-resolver.git`
 
 `$  cd ensembl-web-resolver`
 
 `$ mv sample-env .env`
 
 `$  docker-compose -f docker-compose.yml up`

 ### Deploy the app and run docker-compose:
 Some urls that are available after deployment on your local machine:
 
 http://localhost:8001/id/ENSG00000127720
 
 http://localhost:8001/id/ENSG00000127720.3

### Running application in Local

From the project root directory run the following commands

`$ mv sample-env .env`

`$ python3 -m venv venv`

`$ source venv/bin/activate`

`$ pip install -r requirements.txt`

`$ python3 -m uvicorn app.main:app --port 8001 --reload`

### Run unit tests:
```
python -m unittest tests.test_resolver
python -m unittest tests.test_rapid
```
