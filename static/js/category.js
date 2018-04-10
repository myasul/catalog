/* Controllers of Login Modal */

$("[data-popup-open]").click(function(event) {
    targeted_popup_class = $(this).attr("data-popup-open");
    $(`[data-popup=${targeted_popup_class}]`).fadeIn(350);
    event.preventDefault();
});

$("[data-popup-close]").click(function(event) {
    targeted_popup_class = $(this).attr("data-popup-close");
    $(`[data-popup=${targeted_popup_class}]`).fadeOut(350);
    event.preventDefault();
});

/* For Google OAuth2 login */

$(".login").click(function() {
    $.ajax({
        type: "GET",
        url: "/login",
        success: function(result) {
            $(".login-popup").attr("data-token", result);
        }
    });
});

function start() {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({
            client_id: "1023941705843-jhhhoait4klmlqamos53j3gd6q4dtito.apps.googleusercontent.com",
        });
    });
}

$("#signinButton").click(function(event) {
    auth2.grantOfflineAccess().then(signInCallback);
    event.preventDefault();
});

function signInCallback(authResult) {
    if (authResult["code"]) {

        // Hide the sign-in button now the user has been authorized.
        //$("#signinButton").attr("style", "display: none");
        state = $(".login-popup").attr("data-token");

        // Send the one-time-use code and handle accordingly
        $.ajax({
            type: 'POST',
            url: `/gconnect?state=${state}`,
            processData: false,
            data: authResult["code"],
            contentType: 'application/octet-stream, charset=utf-8',
            success: function(result) {
                if (result) {
                    $(".login-popup").fadeOut(150);
                    $(".login > a").html("Logout")
                }
            }
        });
    } else if (authResult["error"]) {
        console.log("There was an error: " + authResult["error"]);
    } else {
        console.log("Failed to make a server-side all. Check you configuration and console.");
    }
}

$(".category").click(function() {
    // Would return all of the items of the clicked category 
    // which will be displayed in the webpage.
    // This would also add delete and edit button for that category.

    $(".category-details-header").html($(this).html());
    category_id = $(this).attr("data-id");

    $(".item").html("");
    display_items_and_buttons(category_id);
});

function load_items_oncancel() {
    category_id = $(".load-category-details").attr("data-category-id");
    $(".category-details-header").html($(".load-category-details").attr("data-category-name"));
    display_items_and_buttons(category_id);
}

function display_items_and_buttons(category_id) {
    $(".item-per-category").html(request_category_items(category_id));
    $(".edit_and_delete_buttons").html(add_edit_and_delete_buttons(category_id));
};

function add_edit_and_delete_buttons(category_id) {
    edit_category_link = `<a class="button" href="/categories/${category_id}/edit">Edit</a> `;
    delete_category_link = `<a class="button" href="/categories/${category_id}/delete">Delete</a>`;

    return html_string = `${edit_category_link}${delete_category_link}`;
}

function request_category_items(category_id) {
    $.ajax({
        type: "GET",
        url: `/api/categories/${category_id}/`,
        async: false,
        success: function(result) {
            item_list = "";

            $.each(result["Category_Items"], function() {
                name = this["name"];
                item_id = this["id"];
                link = `/categories/${category_id}/items/${item_id}`
                item_list += `<a href=${link}>${name}</a><br>`;
            });
        }
    });
    return item_list;
}