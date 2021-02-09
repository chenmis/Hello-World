
fetch("https://reqres.in/api/users?page=1").then(response => response.json())
    .then(resJSON => extractData(resJSON.data)).catch(err => console.log(err));

function extractData (users){
    const mainDiv = document.querySelector("main");
    for (let user of users){
        const userDiv = document.createElement("section");
        userDiv.innerHTML = `
        <div class="gallery">
          <a target="_blank" href="${user.avatar}">
            <img src="${user.avatar}" alt="Cinque Terre" width="600" height="400">
          </a>
          <br>
          <span class="first_name">${user.id}. ${user.first_name}</span>
          <span class="last_name">${user.last_name}</span>
          <br>
          <a href="mailto:${user.email}">${user.first_name}'s mail</a><br>
        </div
        `
        mainDiv.appendChild(userDiv);
    }
}
