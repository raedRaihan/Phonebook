import unittest
import requests

Login=('tim',"password") # this guy has read write privileges
INVALIDLogin=('tim','notpassword')
nonPrivlegedLogin=("bob","123") # this guy only has read privileges


def readInFile(fileName):
    output=[]
    with open(fileName, 'r') as file: 
        lines = file.readlines() 
        output = [line.strip("\n") for line in lines] 
    return output





class TestCalc(unittest.TestCase):#inherits from unittest
    
    
    def test_listBook(self):
        response = requests.get("http://localhost:8000/PhoneBook/list",auth=Login)
        
        if(self.assertEqual(response.ok,True)):
            pass

    def test_add_ValidNames(self):
      
        response = requests.post("http://localhost:8000/PhoneBook/clear")

        names=readInFile("validNames.txt")
        testNumbers=["11111","67890","11123","41516","17181","92021"]
        i=0
        for name in names:
            person_data  = {
                "full_name": name,
                "phone_number": testNumbers[i]
            }
            i+=1

            response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
            if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
                pass
    
    def test_add_ValidNumbers(self):
      
        response = requests.post("http://localhost:8000/PhoneBook/clear")
        numbers=readInFile("validPhoneNumbers.txt")
        for number in numbers:
            person_data  = {
                "full_name": "Test Name",
                "phone_number": number
            }
            response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
            if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
                pass 

        
    
    def test_InValidNames(self):
        response = requests.post("http://localhost:8000/PhoneBook/clear")
        names=readInFile("inValidNames.txt")
        testNumbers=["12345","67890","11123","41516","17181","92021"]
        i=0
        for name in names:
            person_data  = {
                "full_name": name,
                "phone_number": testNumbers[i]
            }
            i+=1

            try:
                response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
                response.raise_for_status() 
                if(self.assertEqual(response.ok,False)):
                    pass

            except requests.exceptions.HTTPError as e:
                if(self.assertEqual(str(e),"400 Client Error: Bad Request for url: http://localhost:8000/PhoneBook/add")):
                    pass 

    def test_InValidNumbers(self):
       
        response = requests.post("http://localhost:8000/PhoneBook/clear")
        numbers=readInFile("inValidPhoneNumbers.txt")
        for number in numbers:
            person_data  = {
                "full_name": "Test Name",
                "phone_number": number
            }

            try:
                response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
                response.raise_for_status()
                if(self.assertEqual(response.ok,False)):
                    pass

            except requests.exceptions.HTTPError as e:
                if(self.assertEqual(str(e),"400 Client Error: Bad Request for url: http://localhost:8000/PhoneBook/add")):
                    pass 
    
    def test_delete_by_name(self):
        response = requests.post("http://localhost:8000/PhoneBook/clear")


        person_data  = {
                "full_name": "Bruce Schneier",
                "phone_number": "(703)111-2121"
            }
        
        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly

        # now we delete the user
        try:
            input_data= {
                "full_name": "Bruce Schneier",
            }
            response = requests.put("http://localhost:8000/PhoneBook/deleteByName", auth=Login, json=input_data)
            if(self.assertEqual(list(response.json().values())[0],"Person deleted successfully")):
                pass
        except requests.exceptions.HTTPError as e:
            if(self.assertEqual(1,0)):# have a faliure since that person is not found
                pass

        # trying a user that doesn't exist
        
        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly

        try:
            input_data  = {
                "full_name": "Bud Schneier",
            }

            response = requests.put("http://localhost:8000/PhoneBook/deleteByName", auth=Login, json=input_data)
            if(list(response.json().values())[0]=="Person not found in the database"):
                pass
            else:
                end=1/0
        except:
            if(self.assertEqual(1,0)): # there should be an error that user does not exist 
                pass
    
    def test_delete_by_number(self):
        response = requests.post("http://localhost:8000/PhoneBook/clear")

     

        person_data  = {
                "full_name": "Bruce Schneier",
                "phone_number": "(703)111-2121"
            }
        
        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly

        # now we delete the user
        try:
            response = requests.put("http://localhost:8000/PhoneBook/deleteByNumber", auth=Login, json={"phone_number": "(703)111-2121"})
            if(self.assertEqual(list(response.json().values())[0],"Person deleted successfully")):
                pass
        except requests.exceptions.HTTPError as e:
            if(self.assertEqual(1,0)):# have a faliure since that person is not found
                pass

        # trying a user that doesn't exist
        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)
        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly

        try:
         
            response = requests.put("http://localhost:8000/PhoneBook/deleteByNumber", auth=Login, json={"phone_number": "(703)222-2121"})
            if(list(response.json().values())[0]=="Person not found in the database"):
                pass
            else:
                end=1/0
        except:
            if(self.assertEqual(1,0)): # there should be an error that user does not exist 
                pass
    
    def test_incorrectLogin(self):
        
        
        person_data  = {
                "full_name": "Test Name",
                "phone_number": "(703)111-2121"
            }
        response = requests.post("http://localhost:8000/PhoneBook/clear")


        response = requests.get("http://localhost:8000/PhoneBook/list",auth=INVALIDLogin)
            
        if(self.assertEqual(list(response.json().values())[0],"Incorrect username or password")):
            pass

        response = requests.post("http://localhost:8000/PhoneBook/add", auth=INVALIDLogin, json=person_data)

        if(self.assertEqual(list(response.json().values())[0],"Incorrect username or password")):
            pass

        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)

        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly
        
        response = requests.put("http://localhost:8000/PhoneBook/deleteByNumber", auth=INVALIDLogin, json={"phone_number": "(703)111-2121"})

        if(self.assertEqual(list(response.json().values())[0],"Incorrect username or password")):
            pass

        response = requests.put("http://localhost:8000/PhoneBook/deleteByName", auth=INVALIDLogin, json={"full_name": "Test Name"})

        if(list(response.json().values())[0]=="Incorrect username or password"):
                pass
        
    def test_user_privleges(self):
        
        person_data  = {
                "full_name": "Test Name",
                "phone_number": "(703)111-2121"
            }
        response = requests.post("http://localhost:8000/PhoneBook/clear")
        madeError=False
        try:
            response = requests.post("http://localhost:8000/PhoneBook/add", auth=nonPrivlegedLogin, json=person_data)
            
            if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
                pass
            madeError=True
                
        except:
            pass
        
        if(madeError):
            a=1/0 # Person does not have appopriate privileges
        
        response = requests.post("http://localhost:8000/PhoneBook/add", auth=Login, json=person_data)

        if(self.assertEqual(list(response.json().values())[0],"Person added successfully")):
            pass# make sure we added the person properly
        
        response = requests.put("http://localhost:8000/PhoneBook/deleteByNumber", auth=nonPrivlegedLogin, json={"phone_number": "(703)111-2121"})


        if(list(response.json().values())[0]=="Caller not authorized to read entries"):
            pass
        else:
            a=1/0 # caller should not have been able to delete that person

        response = requests.put("http://localhost:8000/PhoneBook/deleteByName", auth=nonPrivlegedLogin, json={"full_name": "Test Name"})

        if(list(response.json().values())[0]=="Caller not authorized to read entries"):
            pass
        else:
            a=1/0 # caller should not have been able to delete that person




if __name__ == '__main__':
    unittest.main()