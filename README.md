# Item Catalog 
__Udacity's Full Stack Web Developer Degree Project - Item Catalog__

__Description:__

This application provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

__Pre-requisites:__
* Install Python 3. http://docs.python-guide.org/en/latest/starting/installation/
* Install PostgreSQL. http://postgresguide.com/setup/install.html
* Install other dependencies. Kindly run the command below to install all dependencies:
  `pip install -r requirements.txt`
* Set up Google Sign-in:
  1. Setup Google's OAuth. Please follow the steps in the link: https://www.appypie.com/faqs/how-can-i-get-my-google-acount-client-id-and-client-secret-key
  1. Save the client ID and client secret by downloading it as JSON file and naming it as __client_secret_google.json__. Save it under the same level as catalog.py.
  1. Add the client ID inside footer.html. Include it in `<span class="g-signin" data-scope="openid email profile" data-clientid="insert client ID" ...> `

__Deployment:__

Make the file executable - Linux/Unix/Mac
1. Make the file executable by running `chmod +x myscript.py` or `chmod 755 scriptfile`
1. Run the file in the terminal by running `./catalog.py`

Run the file using the python command
1. Go to the directory where catalog.py is.
1. Run the program by executing the command `python catalog.py`

__Features:__
* You can use your google account to log in the website.
* You can create your own categories and items.
* You can update items so that it will be transferred to another category.
* Name and description is necessary for every item. 
* You have an option to put an image of your choice in your created items. If you did not specify any image there will be a default image that you can update later on.
* Names are up to 80 characters long. Names with greater than 80 characters long will be truncated.
* Description are up to 1000 characters long. Description with greater than 1000 characters long will be truncated.

__JSON Endpoints:__

You can use the following URLs to retrieve specific information about categories and items that you need.
* http://localhost:5000/api/categories - This will retrieve all categories and their respective items.
* http://localhost:5000/api/categories/insert_category_id -  This will retrieve a specific category with its respective items. e.g. http://localhost:5000/api/categories/1
* http://localhost:5000/api/categories/insert_category_id/insert_item_id - This will retrieve a specific item under a specific category e.g. http://localhost:5000/api/1/3

Enjoy using the Item Catalog website! :)
