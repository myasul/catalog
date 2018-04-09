$(".category").click(function(event) {
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