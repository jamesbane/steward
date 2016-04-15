# Steward
A web application to provide automation solutions.

### stew·ard
/ˈst(y)o͞oərd/  
*noun:* an official appointed to supervise arrangements or keep order at a large public event  
*verb:* manage or look after (another's property).


## Development Requirements
A virtual environment for python is **strongly** recommended!

### Ubuntu Packages
```
apt-get install git python3 python3-dev python3-virtualenv nodejs-legacy npm postgresql-9.5 postgresql-server-dev-9.5 redis-server redis-tools libsasl2-dev libldap2-dev libssl-dev
```

### Virtual Environment
```
virtualenv -p python3 venv
source venv/bin/activate
```

### NPM Packages
```
npm install bower
```

### Bower Packages
```
bower install
```

### Python Packages
```
pip install -r requirements.txt
```

### PostgreSQL
The database user must be a superuser in order for the initial migration to work:
```
-- Create a new user:
createuser --superuser <user_name>
-- Alter an existing user:
ALTER ROLE <user_name> SUPERUSER;
```
