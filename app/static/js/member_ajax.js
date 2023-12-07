const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

$(document).on("click", ".open-Dialog", function () {
    let member_name = $(this).data('member-name')
    let url = $(this).data('url')

    $(".modal-body").html("Are you sure you want to delete member: " + member_name)
    let id = $(this).data('id')


    $(document).on("click", "#deleteButton", function () {
        $.ajax({
            type: "POST",
            headers: { 'X-CSRFToken': csrftoken },
            url: url,
            data: {},
            success: () => {
                $(`#${id}`).remove()
            }
        });
    })
});

