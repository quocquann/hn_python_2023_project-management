$(document).ready(function () {
    $(".add-member").on("click", function () {
        const csrftoken = $(this).find('[name=csrfmiddlewaretoken]').val();
        let user_id = $(this).data("user-id")

        $.ajax({
            type: "POST",
            headers: {'X-CSRFToken': csrftoken},
            data: {
                'user_id': user_id,
            },
            success: (res) => {
                let btn = $(`#btn-${user_id}`)
                btn.text('Success')
                btn.removeClass('add-member')
            }
        });

    });
})
