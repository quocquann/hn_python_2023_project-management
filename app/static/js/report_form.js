
let did = document.querySelector("#did")
let problem = document.querySelector("#problem")
let willDo = document.querySelector("#will-do")
let content = document.querySelector("#content")
let date = document.querySelector("#date")

let submitBtn = document.querySelector("#submitBtn")
let form = document.querySelector("#create-form")


date.value = new Date(Date.now()).toISOString().split("T")[0]

submitBtn.onclick = (event) => {
    event.preventDefault()
    str = did.value + "\n\n" + problem.value + "\n\n" + willDo.value
    content.value = str
    form.submit()
}

