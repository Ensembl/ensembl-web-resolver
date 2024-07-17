# Ensembl Web Resolver
The resolver service generates new Ensembl website urls for different features based on their stable ids, as well as other optional parameters.
### Deploy the app and run docker-compose:
 
 `$ git clone https://github.com/Ensembl/ensembl-web-resolver.git`
 `$  cd ensembl-web-metadata-api`
 `$ mv sample-env .env`
 `$  docker-compose -f docker-compose.yml up`
 
 ### Deploy the app and run docker-compose:
 Some urls that are available after deployment on your local machine:
 http://localhost:8001/id/ENSG00000127720
 http://localhost:8001/id/ENSG00000127720.3
### Run unit tests:
