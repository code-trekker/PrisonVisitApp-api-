from prisonapp import app
import os


port = os.getenv('PORT', '5000')

if __name__ == '__main__':
    #app.run()
    app.run(host='0.0.0.0', port=int(port))

