# Instructions for Developers of this Project

## Structure

  Tests are in the /test folder
  
  Resources used for the front-end and interactive components are in the /resources folder
  
  All documents, including our proposal and our class diagram are in the /docs folder 

## Testing

  Firstly install: /opt/homebrew/bin/python3 -m pip install pytest --break-system-packages
  
  Make sure you are running the tests from your parent directory where both 303MUD and COMP303_Project are located:

    1. To run tests, write this on the commandline: python3 -m pytest COMP303_Project/test
    2. To ignore deprecation warnings: python3 -m pytest -W ignore::DeprecationWarning COMP303_Project/test 
    3. To test a specific file: python3 -m pytest COMP303_Project/test/specificFile.py
