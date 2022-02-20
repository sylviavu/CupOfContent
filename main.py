import requests
from bs4 import BeautifulSoup    # Python library to pull data out of HTML/XML files
import redis
import smtplib
# MIME: Multipurpose Internet Mail Extensions
# Indicates the nature/format of a document
from email.mime.multipart import MIMEMultipart    # Deals with multiple non-text email attachments
from email.mime.text import MIMEText    # Specifies the MIME type, signifies that we will be using text
from secrets import password
import datetime



class Scraper:
    def __init__(self, keywords):
        # Specify the URL and retrieve all of the text on the page
        self.markup = requests.get('https://news.ycombinator.com/news').text
        self.keywords = keywords
        self.saved_links = []
    

    def parse(self):
        soup = BeautifulSoup(self.markup, 'html.parser')    # Pass in the markup we have created and specify that it is in HTML
        all_links = soup.find_all('a', {'class': 'titlelink'})    # Get links according to class 'titlelink' on website
        for link in all_links:
            for keyword in self.keywords:
                if keyword in link.text:
                    self.saved_links.append(link)


    def save(self):
        redis_ref = redis.Redis(host='localhost', port=6379, db=0)
        for link in self.saved_links:
            redis_ref.set(link.text, str(link))


    def email(self):
        # Get all links from the redis db
        redis_ref = redis.Redis(host='localhost', port=6379, db=0)
        relevant_links = [redis_ref.get(link) for link in redis_ref.keys()]

        # email
        fromEmail = 'cupofcontentbot@gmail.com'
        toEmail = 'sylvia@gmail.com'

        msg = MIMEMultipart('alternative')    # Tell the email client to display both plain text and links correctly
        msg['Subject'] = "Link"
        msg["From"] = fromEmail
        msg["To"] = toEmail

        html = """
            <h4> %s Here's your Cup of Content for today: </h4>
            
            %s
        """ % (len(relevant_links), '<br/><br/>'.join(relevant_links))

        mime = MIMEText(html, 'html')

        msg.attach(mime)

        try:
            mail = smtplib.SMTP('smtp.gmail.com', 587)
            mail.ehlo()
            mail.starttls()    # Encrypts the username, password, and at least some of the message contents
            mail.login(fromEmail, password)
            mail.sendmail(fromEmail, toEmail, msg.as_string())
            mail.quit()
            print('Email sent!')
        except Exception as e:
            print('Something went wrong... %s' % e)

        # Clear Redis db to prevent sending the same articles
        redis_ref.flushdb()


s = Scraper(['database'])
s.parse()
s.save()
if datetime.datetime.now().hour == 8:
    s.email()








