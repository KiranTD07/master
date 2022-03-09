#  **REUSABLE FUNCTIONAL AUTOMATION TESTING**


language: 
Python
Selenium

install:
    
  - python - "3.xx"
  - Visit [Python](https://www.python.org/downloads/) and choose your version. We have chosen Python version 3.8.10.

 
Note:
    user need to execute in local machine,
  - Install Pycharm 
  - 


script:
  - py.cleanup -p && py.test --environment=staging -v


**Execution Steps:**

    Install Python (3.xx) versions 

    Install pip3

# PJSIP Installation Instructions 

Downloaded the pj from the official website, you should have a file similar to * pjproject-x.x.tar.bz2 *, x.x being the PJSIP version.

To download, you can access the [project page](https://www.pjsip.org/) and click on (Download)[https://www.pjsip.org/download.htm].

Run the following commands:

    $ sudo apt install build-essential python3-dev libasound2-dev
    $ tar -xf pjproject-x.x.tar.bz2 && cd pjproject-x.x/
    $ export CFLAGS="$CFLAGS -fPIC"
    $ ./configure --enable-shared
    $ make dep
    $ make
    $ sudo make install

With this you already have PJSIP installed on your machine. To work with pysua in python 3, run the following commands:

    $ sudo apt install python3-dev
    $ cd pjproject-x.x/pjsip-apps/src/ 
    $ git clone https://github.com/mgwilliams/python3-pjsip.git 
    $ cd python3-pjsip
    $ python3 setup.py build
    $ sudo python3 setup.py install

To test the pjsua is installed directly in python:

    $ python3
    Python 3.8 (default, Nov 23 2017, 16:37:01)
    [GCC 5.4.0 20160609] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import pjsua
    >>>

# Pre-requisite:

# General :
- In config file,
  - In [API_credentials] section:
    - api_key =` <enter the API Key>`
    - api_token = `<enter the API token>`
  - In [Domain] section:
    - Subdomain = `<enter the Subdomain>`
    - CallerId =`<enter the CallerId>`
    - Account_sid = `<enter the Account_sid>`
    - AWS_Link = `<enter the status call back link>`
  - In [SIP_Account] section:
  - reg_uri = `<enter the regestration uri>`
  - proxy_reg_uri = `<enter the regestration uri "regestration uri;transport=tls;lr">`
  - sip_id1 =<enter the sip user1 id >
  - user1 = <enter the username>
  - password1 = = <enter the password1>
  - sip_id2 = <enter the sip user 2  id >
  - user2 = <enter the username 2>
  - password2 = <enter the user password2>


- Execution
  - Navigate to TestRunner package an open the TestData_production.csv file
  - Select the Testcases by updating Y (Y-Yes) for include and N (No) exclude  in Run column
  - Open the Terminal in project directory    
  - Execute the below command : 
       py.cleanup -p && py.test   --environment=staging