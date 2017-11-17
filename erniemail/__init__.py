import datetime
import smtplib
import socket

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def notify(activity, recipient, sender):

    string = u"""New Activity Found!

    Started: {4}
    Distance: {5}

    Is Negative Split: {0}
    Negative Split_depth: {1}

    Notes: {2}
    Activity Type: {3}
    """.format(activity['is_negative_split'], activity['negative_split_depth'],
               activity['notes'], activity['activity_type'],
               activity['verbose_starttime'], activity['verbose_distance'])

    body = "{0}".format(string)
    subject = "New Activity Processed"
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # Create the body of the message (a plain-text and an HTML version).
    text = "{0}".format(body)
    html = u"""\
    <html>
      <head></head>
      <body>
      <p>
      {0}
        </p>
      </body>
    </html>
    """.format(body.replace("\n", "<br/>"))

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP("localhost")
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()
