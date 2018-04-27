/**
 * Created by Lee on 3/12/2018.
 */
var username = $("#username").val();
var password = $("#password").val();

function make_base_auth(user, password) {
  var tok = user + ':' + password;
  var hash = btoa(tok);
  return "Basic " + hash;
}

var auth = make_base_auth(username,password);

function login() {
    $.ajax({
        url: "http://127.0.0.1:5000/login/",
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify({
            'username': username,
            'password': password
        }),
        method: "GET",
        dataType: "json",
        crossDomain: true,
        headers: {
            'Authorization' : 'Basic ' + btoa(username + ':' + password)
        },
        // beforeSend: function (xhr) {
        //     xhr.setRequestHeader("Authorization", auth)
        // },
        success: function(resp) {
            console.log("success");
            localStorage.setItem('token', resp.token);
            window.location.replace('landing_visitor.html');
            alert.message('login success!')
        },
        error: function () {
            console.log('error')
        }
    })
}

function viewAll(){
    table();
    viewVis();
    showRes();
 }

function viewVis(){

    $("#view_id").show(); //Id ni siya na gamiton sa html

$.ajax({
          url: 'http://127.0.0.1:5000/Visitors/',
          type: "GET",
          dataType: "json",
          crossDomain: true,
           headers: {
                'x-access-token': tokens
            },
          success: function(resp) {

            if (resp.status  === 'ok') {
               for (i = 0; i < resp.count; i++) {
                              firstname = resp.entries[i].firstname;
                              middlename = resp.entries[i].middlename;
                              lastname = resp.entries[i].lastname;
                              age = resp.entries[i].age;
                              contact = resp.entries[i].contact;
                              address = resp.entries[i].address;
                              birthday = resp.entries[i].birthday;
                              status = resp.entries[i].status;
                              $("#view_id").append(showRes(firstname,middlename,lastname,age,contact,address,birthday,status));
               }
            } else {
                $("#view_id").html("");
               alert('No Data')
            }
          }
      });
}

function showRes(firstname,middlename,lastname,age,contact,address,birthday,status)
{
   return '<div class="widget-content">'+
            '<table class="table table-striped table-bordered" id="view_res">'+
                '<tbody><tr class="edit" id="details">'+
                    '<td>'+ firstname +'</td>'+
                    '<td>'+ middlename +'</td>'+
                    '<td>'+ lastname +'</td>'+
                    '<td>'+ age +'</td>'+
                    '<td>'+ contact +'</td>'+
                    '<td>'+ address +'</td>'+
                    '<td>'+ birthday +'</td>'+
                    '<td>'+ status +'</td>'+
                '</tr></tbody>' +
            '</table>' +
       '</div>'
}


function table()
{
     $("table.table-bordered").html('<thead><tr>' +
            '<th>First Name</th>' +
            '<th>Middle Name</th>' +
            '<th>Last Name</th>' +
            '<th>Age</th>' +
            '<th>Contact Number</th>' +
            '<th>Address</th>' +
            '<th>Birth Date</th>' +
            '<th>Account Status</th>' +
            '</tr></thead>')
}
