# AutoAnnotate

AutoAnnotate is a web-based machine-learning assisted image annotation app.
Users upload their own images and can both automatically and manually label
them with our tools for training computer vision models.
This is a repository with the final files for AutoAnnotate app.

To run this application locally using the Flask test HTTP server:

Create a self-signed certificate, that is, create files cert.pem and key.pem.
To do that, issue this command:
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

When prompted, feel free to skip entering all values by pressing the ENTER key.

Run the test server
   python runserver.py

Browse to https://localhost:5000
