# Spartan_Server

### Project Organization
Each separate set of APIs are grouped into separate .py files based on objects. For example, all of the HTTP calls relating to users (creating new, updating info, etc)
are grouped into `users.py`. Similarly, all of the HTTP calls for listings (creating new, updating info, uploading pics) in the database are grouped into `listings.py`. 

To signal these functional distinctions in the methods, each file is given a special HTTP extension. For example, all API calls relating to users should be sent to `http://bygo-client-server.appspot.com/users/*` where `*` is the name of desired function. See the documentation in the Workflows section for more exmaples.



#################################################
#################################################
#################################################
############## TODO: FIX WORKFLOWS ##############
#################################################
#################################################
#################################################


appcfg.py -A molten-unison-112921 update app.yaml 


curl -H "Content-Type: application/json" -X POST -d @json.txt http://molten-unison-112921.appspot.com/user/create
###################################################

########### USER FUNCTIONS ##############
### Create User
curl -H "Content-Type: application/json" -X POST -d "{\"first_name\":\"Olivia\", \"last_name\":\"Park\", \"email\":\"olivia@bygo.io\", \"phone_number\":\"7894561230\", \"password\":\"\", \"signup_method\":\"Facebook\", \"facebook_id\":\"111222333\"}" http://molten-unison-112921.appspot.com/user/create


### Deactivate User
curl -X DELETE http://molten-unison-112921.appspot.com/user/deactivate/user_id=5634387206995968

### Delete User from Search API
curl -X DELETE http://molten-unison-112921.appspot.com/user/delete_from_search/user_id=5634387206995968

### Reactivate User
curl -H "Content-Type: application/json" -X POST -d {} http://molten-unison-112921.appspot.com/user/reactivate/user_id=5634387206995968

### Update User
curl -H "Content-Type: application/json" -X POST -d "{\"first_name\":\"Sayan\", \"last_name\":\"Roychowdhury\", \"email\":\"sayan@bygo.io\", \"phone_number\":\"0123456789\"}" http://molten-unison-112921.appspot.com/user/update/user_id=5634387206995968

### Add/Update User profile picture
curl -X POST -F "filename=profile_picture.jpg" -F "userfile=@C:/Users/Sayan/Desktop/rsz_dsc_0780.jpg" http://molten-unison-112921.appspot.com/user/create_user_image/user_id=5634387206995968

### Delete User Profile Picture
curl -X DELETE http://molten-unison-112921.appspot.com/user/delete_user_image/path=5752571553644544/user_id=5634387206995968

### Get User Data (also returns a media link to their profile picture)
curl http://molten-unison-112921.appspot.com/user/user_id=5634387206995968




########### LISTING FUNCTIONS ##############
### Create Listing
curl -H "Content-Type: application/json" -X POST -d "{\"category_id\":\"5713573250596864\", \"name\":\"Garbage Headphones\", \"item_description\":\"This is a test desc.\", \"total_value\":\"75\", \"hourly_rate\":\"7.5\", \"daily_rate\":\"15\", \"weekly_rate\":\"30\"}" http://molten-unison-112921.appspot.com/listing/create/user_id=5752571553644544

### Get suggested rates for a listing given its total value
curl http://molten-unison-112921.appspot.com/listing/suggested_rates/total_value=95.5

### Delete Listing
curl -X DELETE http://molten-unison-112921.appspot.com/listing/delete/listing_id=5749563331706880

### Update Listing
curl -H "Content-Type: application/json" -X POST -d "{\"category_id\":\"5713573250596864\", \"name\":\"Knockoff Headphones\", \"item_description\":\"I AM A LIAR\", \"total_value\":\"75\", \"hourly_rate\":\"7.5\", \"daily_rate\":\"15\", \"weekly_rate\":\"30\", \"status\":\"Unlisted\"}" http://molten-unison-112921.appspot.com/listing/update/listing_id=5749563331706880

### Add listing image
curl -X POST -F "filename=belt.jpg" -F "userfile=@C:/Users/Sayan/Desktop/8-4-10-logitech60037.jpg" http://molten-unison-112921.appspot.com/listing/new_listing_image/listing_id=5657382461898752

### Delete listing image
curl -X DELETE http://molten-unison-112921.appspot.com/listing/delete_listing_image/path=5682617542246400/40mmOLChntSglLp2686GovBlkSnp-2.jpg

### Get a listing's data
curl http://molten-unison-112921.appspot.com/listing/get_info/listing_id=5657382461898752

### Get User's Listings (user == owner)
curl http://molten-unison-112921.appspot.com/listing/get_listings/user_id=5752571553644544

### Get User's Rented Listings (user == renter)
curl http://molten-unison-112921.appspot.com/listing/get_rented_listings/user_id=5752571553644544



########### MEETING LOCATION FUNCTIONS ##############
### Create Meeting Location
curl -H "Content-Type: application/json" -X POST -d "{\"google_places_id\":\"ChIJmc6iNkfXDIgRqE-VN6vAsbI\", \"name\":\"Home\", \"address\":\"502 E Springfield Ave, Champaign, IL 61820, USA\", \"is_private\":\"True\"}" http://molten-unison-112921.appspot.com/meeting_location/create/user_id=5752571553644544

### Delete Meeting Location
curl -X DELETE http://molten-unison-112921.appspot.com/meeting_location/delete/location_id=5629652273987584

### Update Meeting Location
curl -H "Content-Type: application/json" -X POST -d "{\"google_places_id\":\"ChIJv5lMaT_XDIgRsEtHigVjhEY\", \"name\":\"McDonald's\", \"address\":\"502 E Springfield Ave, Champaign, IL 61820, USA\", \"is_private\":\"False\"}" http://molten-unison-112921.appspot.com/meeting_location/update/location_id=5688424874901504

### Get User's Meeting Locations
curl http://molten-unison-112921.appspot.com/meeting_location/get_meeting_locations/user_id=5752571553644544



########### ADVERTISED LISTINGS FUNCTIONS ##############
curl http://molten-unison-112921.appspot.com/advertised_listings/snapshots/user_id=6288801441775616/radius=10

### Search listings by string
curl http://molten-unison-112921.appspot.com/advertised_listings/user_id=6288801441775616/radius=10/search=stick%20usb



########### RENT EVENT FUNCTIONS ##############
### Propose a rent request
curl -H "Content-Type: application/json" -X POST -d @json.txt http://molten-unison-112921.appspot.com/rent_event/propose/listing_id=5657382461898752/renter_id=5725851488354304

### Accept a rent request
curl -H "Content-Type: application/json" -X POST -d "{\"time\":\"2016 03 20 15:30:00\", \"location_id\":\"5688424874901504\"}" http://molten-unison-112921.appspot.com/rent_event/accept/rent_event_id=5202656289095680

### Get a user's rent requests (requests from other using asking to rent an item)
curl http://molten-unison-112921.appspot.com/rent_event/get_rent_events/user_id=5752571553644544

### Get a specific rent request
curl http://molten-unison-112921.appspot.com/rent_event/get_rent_event/rent_event_id=5202656289095680



########### MEETING EVENT FUNCTIONS ##############
### Get a specific meeting event
curl http://molten-unison-112921.appspot.com/meeting_event/get_meeting_event/meeting_event_id=5174714574045184	

### Get a list of user's meeting event
curl http://molten-unison-112921.appspot.com/meeting_event/get_user_meeting_events/user_id=5752571553644544