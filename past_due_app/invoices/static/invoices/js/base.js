import { login } from "./login.js";

document.addEventListener("DOMContentLoaded", () => {
    
    const loginButton = document.getElementById("login-button");
    const loginStatus = document.getElementById("login-status");
    
    loginButton.addEventListener("click", async (event) => {
        console.log("Login button was clicked!");
        
        const data = await login();

        if (data) {
          loginStatus.innerText = data["status"];
        } else {
          loginStatus.innerText = "Login failed."
        }
    });
    
});