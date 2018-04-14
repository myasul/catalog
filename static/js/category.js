/* Login session */
$(window).ready(function() {
    logged_in = $(".category-container").attr("data-logged-in");
    if (logged_in == 'True') {
        $(".login").append(`<a data-popup-open="logout-popup">Logout</a>`);
    } else {
        $(".login").append(`<a data-popup-open="login-popup">Login</a>`);
    }
});

/* Controllers of Login Modal */

$(".login").on('click', '[data-popup-open]', function(event) {
    targeted_popup_class = $(this).attr("data-popup-open");
    $(`[data-popup=${targeted_popup_class}]`).fadeIn(350);
    event.preventDefault();
});

/* Controller of Delete Modal */
$(".category-container").on('click', '[data-popup-open]', function(event) {
    targeted_popup_class = $(this).attr("data-popup-open");
    category_id = $(this).attr("data-category-id");
    item_id = $(this).attr("data-item-id");
    data_type = $(this).attr("data-type");

    error_msg = "Are you sure you want to delete this item?";
    if (data_type == "category") {
        error_msg = "<p>Are you sure you want to delete this category?</p>";
        item_count = request_item_count(category_id);
        if (item_count > 0) {
            error_msg += "<p>There are still items in this category. Deleting this category would delete the items as well.</p>"
        }
    }

    $(".delete-message").html(error_msg);
    $(".delete").attr("data-category-id", category_id);
    $(".delete").attr("data-item-id", item_id);
    $(".delete").attr("data-type", data_type);
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

var auth2

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
                    $(".login-popup").fadeOut(50);
                    $(".login > a").html("Logout");
                    $(".login > a").attr("data-popup-open", "logout-popup");
                    window.location.replace("/categories");
                }
            }
        });
    } else if (authResult["error"]) {
        console.log("There was an error: " + authResult["error"]);
    } else {
        console.log("Failed to make a server-side all. Check you configuration and console.");
    }
}

$(".logout").click(function() {
    $.ajax({
        type: "GET",
        url: "/gdisconnect",
        success: function(result) {
            if (result) {
                $(".logout-popup").fadeOut(10);
                $(".login > a").html("Login");
                $(".login > a").attr("data-popup-open", "login-popup");
                window.location.replace("/categories");
            }
        }
    });
})

$(".delete").click(function() {
    type = $(this).attr("data-type");
    category_id = $(this).attr("data-category-id");
    item_id = $(this).attr("data-item-id");

    url = `/categories/${category_id}/items/${item_id}/delete/`;
    url_redirect = `/categories/${category_id}`;
    if (type == "category") {
        url = `/categories/${category_id}/delete/`;
        url_redirect = "/categories";
    }

    $.ajax({
        type: "POST",
        url: url,
        success: function(result) {
            $(".delete-popup").fadeOut(10);
            window.location.replace(url_redirect);
        }
    });
})

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
    if (is_authorized(category_id)) {
        $(".category-details").append(`<div class="category_buttons modify_item_buttons"></div>`);
        $(".modify_item_buttons").html(modify_item_buttons(category_id));
    } else {
        $(".modify_item_buttons").remove();
    }
};

function modify_item_buttons(category_id) {
    edit_category_link = `<a class="button" href="/categories/${category_id}/edit">Edit</a>`;
    delete_category_link = `<a class="button" data-category-id="${category_id}" data-popup-open="delete-popup" data-type="category">Delete</a>`;
    create_item_link = `<a class="button" href="/categories/${category_id}/items/create/">Create Item</a>`;
    return `${edit_category_link} ${delete_category_link} ${create_item_link}`;
}

function is_authorized(category_id) {
    authorized = false;
    $.ajax({
        type: "GET",
        url: `/api/categories/authorized/${category_id}`,
        async: false,
        success: function(result) {
            console.log(result)
            authorized = result;
        }
    });
    return authorized;
}

function request_category_items(category_id) {
    $.ajax({
        type: "GET",
        url: `/api/categories/${category_id}`,
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
};

function request_item_count(category_id) {
    $.ajax({
        type: "GET",
        url: `/api/categories/item_count/${category_id}`,
        async: false,
        success: function(result) {
            item_count = result;
        }
    });
    return item_count;
};