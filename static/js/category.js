$(".category").click(function(event) {
    // Would return all of the items of the clicked category 
    // which will be displayed in the webpage
    $(".category-details-header").html($(this).html());
    category_id = $(this).attr("data-id");
    $.ajax({
        type: "GET",
        url: `/api/categories/${category_id}/`,
        success: function(result) {
            item_list = "";

            $.each(result["Category_Items"], function() {
                name = this["name"];
                item_id = this["id"];
                link = `/categories/${category_id}/items/${item_id}`
                item_list += `<a href=${link}>${name}</a><br>`;
            });

            $(".item-per-category").html(item_list);
            $(".item").html("");
        }

    });
});