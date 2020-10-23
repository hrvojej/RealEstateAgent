import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np

class SendToGmail:
    def __init__(self, destination, df, serverLogin, serverPss):
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.server.starttls()
        self.serverLogin = serverLogin
        self.serverPss = serverPss
        # don't know how to do it without cleartexting the password and not relying on some json file that you dont git control...
        self.server.login(self.serverLogin, self.serverPss)
        self.destination = destination
        self.df = df

        # Int formatting in padnas.to_html
        num_format = lambda x: '{:,}'.format(x)
        self.formatters = self.build_formatters(num_format)
        self.sendGmail()

    def build_formatters(self, format):
        return {column: format
                for (column, dtype) in self.df.dtypes.iteritems()
                    if dtype in [np.dtype('int64'), np.dtype('float64')] or dtype in [np.dtype('int32'), np.dtype('float64')]
                }


    def sendGmail(self):
        self.msg = MIMEMultipart()
        self.msg['Subject'] = "[NjuškaloPoštar] " + str(len(self.df.index))
        self.msg['From'] = 'njuskalo@postar'

        self.html = """\
           <html>
             <head></head>
             <body>
               {0}
             </body>
           </html>
           """.format(self.df.to_html(formatters=self.formatters))
        part1 = MIMEText(self.html, 'html')
        self.msg.attach(part1)
        self.server.sendmail(self.msg['From'], self.destination, self.msg.as_string())
        return

# lst = [['tom', 25], ['krish', 30],
#        ['nick', 26], ['juli', 22]]
# df_test = pd.DataFrame(lst, columns=['Name', 'Age'])
#
# SendToGmail(destination='hrvojej@gmail.com', df = df_test, serverLogin='hrvojej@gmail.com', serverPss='DarDoh-23')
