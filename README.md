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
curl -H "Content-Type: application/json" -X POST -d "{\"first_name\":\"JJ\", \"last_name\":\"Qi\", \"email\":\"jj@bygo.io\", \"phone_number\":\"4569871231\", \"password\":\"hello_world\", \"signup_method\":\"Phone Number\", \"facebook_id\":\"\"}" http://molten-unison-112921.appspot.com/user/create

### Deactivate User
curl -X DELETE http://molten-unison-112921.appspot.com/user/deactivate/user_id=5717495361044480

### Delete User from Search API
curl -X DELETE http://molten-unison-112921.appspot.com/user/delete_from_search/user_id=5706163895140352

### Reactivate User
curl -X POST -d {} http://molten-unison-112921.appspot.com/user/reactivate/user_id=5717495361044480

### Update User
curl -H "Content-Type: application/json" -X POST -d "{\"first_name\":\"Sayan\", \"last_name\":\"Roychowdhury\", \"email\":\"sayan@bygo.io\", \"phone_number\":\"0123456789\"}" http://molten-unison-112921.appspot.com/user/update/user_id=5634387206995968

### Add/Update User profile picture
curl -X POST -F "filename=profile_picture.jpg" -F "userfile=@C:/Users/Sayan/Desktop/tumblr_mzzprh5Rxw1t41r5fo1_500.png" http://molten-unison-112921.appspot.com/user/create_user_image/user_id=5750790484393984

### Delete User Profile Picture
curl -X DELETE http://molten-unison-112921.appspot.com/user/delete_user_image/user_id=5634387206995968

### Get User Data (also returns a media link to their profile picture)
curl http://molten-unison-112921.appspot.com/user/user_id=5750790484393984

### Create User Home Address
curl -H "Content-Type: application/json" -X POST -d @test_jsons/new_delivery_address.json http://molten-unison-112921.appspot.com/delivery_address/create/user_id=5722467590995968

### Delete User Home Address
curl -X DELETE http://molten-unison-112921.appspot.com/delivery_address/delete/user_id=5634387206995968

### Get User Home Address
curl http://molten-unison-112921.appspot.com/delivery_address/get/user_id=5634387206995968

### Generate Phone Number Verification Code
curl http://molten-unison-112921.appspot.com/verification/phone_number/send_code/user_id=5649521866440704

### Verify Phone Number
curl -H "Content-Type: application/json" -X POST -d "{\"verification_code\":\"547517\", \"user_id\":\"5649521866440704\"}" http://molten-unison-112921.appspot.com/verification/phone_number/check_code



########### LISTING FUNCTIONS ##############
### Create Listing
curl -H "Content-Type: application/json" -X POST -d "{\"user_id\":\"5649521866440704\", \"type_id\":\"5639574185312256\"}" http://molten-unison-112921.appspot.com/listing/create

### Get suggested rates for a listing given its total value
curl http://molten-unison-112921.appspot.com/listing/suggested_rates/total_value=95.5

### Delete Listing
curl -X DELETE http://molten-unison-112921.appspot.com/listing/delete/listing_id=5727389891952640

### Update Listing
curl -H "Content-Type: application/json" -X POST -d "{\"category_id\":\"5713573250596864\", \"name\":\"Knockoff Headphones\", \"item_description\":\"I AM A LIAR\", \"total_value\":\"75\", \"hourly_rate\":\"7.5\", \"daily_rate\":\"15\", \"weekly_rate\":\"30\", \"status\":\"Unlisted\"}" http://molten-unison-112921.appspot.com/listing/update/listing_id=5749563331706880

### Add listing image
curl -X POST -F "filename=ps4.jpg" -F "userfile=@C:/Users/Sayan/Desktop/ps4-634334.jpg" http://molten-unison-112921.appspot.com/listing/create_listing_image/listing_id=5747610597982208

### Delete listing image
curl -X DELETE http://molten-unison-112921.appspot.com/listing/delete_listing_image/path=5682617542246400/40mmOLChntSglLp2686GovBlkSnp-2.jpg

### Get a listing's data
curl http://molten-unison-112921.appspot.com/listing/listing_id=5659118702428160

### Get User's Listings (user == owner)
curl http://molten-unison-112921.appspot.com/listing/get_users_listings/user_id=5634387206995968

### Get User's Rented Listings (user == renter)
curl http://molten-unison-112921.appspot.com/listing/get_users_rented_listings/user_id=5634387206995968



########### ITEM_TYPE FUNCTIONS ##############
### Load Data from JSON file
curl -H "Content-Type: application/json" -X POST -d @test_jsons/item_type_list.json http://molten-unison-112921.appspot.com/item_type/load_data

### Create new Item_Type from JSON file
curl -H "Content-Type: application/json" -X POST -d @test_jsons/new_item_type.json http://molten-unison-112921.appspot.com/item_type/create

### Delete Item_Type
curl -X DELETE http://molten-unison-112921.appspot.com/item_type/delete/item_type_id=5700735861784576

### Create new tag for Item_Type
curl -H "Content-Type: application/json" -X POST -d "{\"tag\":\"Sony\"}"  http://molten-unison-112921.appspot.com/item_type/create_tag/item_type_id=5681777339269120

### Delete tag for Item_Type
curl -X DELETE  http://molten-unison-112921.appspot.com/item_type/delete_tag/item_type_id=5681777339269120/tag=Sony



########### CONSISTENCY CHECK FUNCTIONS #############
### User Consistency Check
curl -X DELETE http://molten-unison-112921.appspot.com/consistency_check/users

### Listing Consistency Check
curl -X DELETE http://molten-unison-112921.appspot.com/consistency_check/listings

### Item Type Consistency Check
curl -X DELETE http://molten-unison-112921.appspot.com/consistency_check/item_types




########### ORDER FUNCTIONS #################
### Create Order
curl -H "Content-Type: application/json" -X POST -d @test_jsons/order.json http://molten-unison-112921.appspot.com/order/create

### Cancel Order
curl -X DELETE http://molten-unison-112921.appspot.com/order/cancel/order_id=5739238230327296

### Get Order
curl http://molten-unison-112921.appspot.com/order/order_id=5197794386116608

### Get a User's Orders
curl http://molten-unison-112921.appspot.com/order/user_id=5634387206995968

### Get Possible Orders
curl http://molten-unison-112921.appspot.com/order/get_possible/user_id=5634387206995968

### Owner Offers their Listing
curl -X POST -d {} http://molten-unison-112921.appspot.com/order/offer_listing/order_id=5197794386116608/listing_id=5152971570544640





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