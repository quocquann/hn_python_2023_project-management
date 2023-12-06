const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

$(document).on("click", ".open-Dialog", function () {
    let task_name = $(this).data('task-name')
    let url = $(this).data('url')
    let id = $(this).data('id')
    $(".modal-body").html("Are you sure you want to delete the task: " + task_name)

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
