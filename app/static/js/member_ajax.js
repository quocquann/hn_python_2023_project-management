const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value

const swalWithBootstrapButtons = Swal.mixin({
    customClass: {
        confirmButton: "btn btn-success",
        cancelButton: "btn btn-danger"
    },
    buttonsStyling: false
})

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
                swalWithBootstrapButtons.fire({
                    title: "Deleted!",
                    text: "Member has been deleted.",
                    icon: "success"
                })
                $(`#${id}`).remove()
            },
            error: () => {
                swalWithBootstrapButtons.fire({
                    title: "Fail",
                    text: "Fail to delete member",
                    icon: "error"
                });
            }
        });
    })
});

