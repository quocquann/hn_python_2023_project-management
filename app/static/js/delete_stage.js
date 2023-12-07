$(document).ready(function () {
    function delete_stage(csrftoken, remove_id, url) {
        const swalWithBootstrapButtons = Swal.mixin({
            customClass: {
                confirmButton: "btn btn-success",
                cancelButton: "btn btn-danger"
            },
            buttonsStyling: false
        });

        swalWithBootstrapButtons.fire({
            title: "Are you sure?",
            text: "You won't be able to revert this!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete it!",
            cancelButtonText: "No, cancel!",
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                $.ajax({
                    type: "POST",
                    headers: {'X-CSRFToken': csrftoken},
                    url: url,
                    data: {},
                    success: (res) => {
                        let stage = res.stage
                        $('.stage-closed').append(`
                            <div class="card text-white bg-secondary mb-3 col-4" style="width: 18rem;"
                             id="stage-${stage.id}">
                            <div class="card-body">
                                <a href="" class="card-title">${stage.name}</a>
                                <p class="card-text">Start date: ${stage.start_date}</p>
                                <p class="card-text">End date: ${stage.end_date}</p>
                                <button class="btn btn-info active-stage" data-stage-id="${stage.id}"
                                        data-project-id="${stage.project}">
                                    Active
                                </button>
                            </div>
                        </div>
                        `)
                        $('#num-stage').text(res.num_stages)
                        $(`#${remove_id}`).remove()

                    }
                });
                swalWithBootstrapButtons.fire({
                    title: "Deleted!",
                    text: "Your stage has been deleted.",
                    icon: "success"
                });
            } else if (
                result.dismiss === Swal.DismissReason.cancel
            ) {
                swalWithBootstrapButtons.fire({
                    title: "Cancelled",
                    text: "Your imaginary stage is safe :)",
                    icon: "error"
                });
            }
        });
    }

    $(".delete-stage").on("click", function () {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        let project_id = $(this).data("project-id")
        let stage_id = $(this).data("stage-id")
        let remove_id = 'stage-' + stage_id
        let url = project_id + "/stages/" + stage_id + "/delete/"
        delete_stage(csrftoken, remove_id, url)
    })
})
