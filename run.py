# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


from weibo import app
import os

app.secret_key = os.urandom(24)
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)