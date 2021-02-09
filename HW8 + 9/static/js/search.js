function load(name) {
    fetch("https://reqres.in/api/users?page=1").then(response => response.json())
    .then(resJSON => extractData(resJSON.data, name)).catch(err => console.log(err));
}

function extractData (users, name){
    let found = false;

    const mainDiv = document.querySelector("main");
    for (let user of users){
        if (name == "" || name.toLowerCase() == user.first_name.toLowerCase()) {
            const userDiv = document.createElement("section");
            userDiv.innerHTML = `
            <div class="gallery">
              <a target="_blank" href="${user.avatar}">
                <img src="${user.avatar}" width="600" height="400">
              </a>
              <br>
              <span class="first_name">${user.id}. ${user.first_name}</span>
              <span class="last_name">${user.last_name}</span>
              <br>
              <a href="mailto:${user.email}">${user.first_name}'s mail</a>
            </div
            `
            mainDiv.appendChild(userDiv);
            found = true;
        }
    }

    if (!found){
        const errorDiv = document.createElement("section");
        errorDiv.innerHTML = "<h3>No users found</h3>";
        mainDiv.appendChild(errorDiv);
    }
}