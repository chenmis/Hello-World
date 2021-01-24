var categories_images =["benda.jpg", "chen_wedding.jpg", "eden_card.jpg", "elia.jpg", "foodapp.jpg", "matnas.jpg", "mich_card.jpg", "nirit-logo.png", "rotem.png", "roza.jpg", "tal_app.png", "track-app-01.jpg", "victor.png", "menu.jpg", "malki.png", "tshirt.jpg"];

function img_change(myDiv){

  var first_element = categories_images.shift();
  categories_images.push(document.getElementById(myDiv).style.backgroundImage.slice(15,-2));
  document.getElementById(myDiv).style.backgroundImage = "url('PORTFOLIO/" + first_element + "')";


}
