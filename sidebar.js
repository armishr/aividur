function createSidebarTemplate() {
  document.write( `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <!-- ... Your existing head content ... -->
        <style>
        /* Add your custom CSS styles here */
        /* Style for the side navbar */
          #sidebar {
              
              top: 0;
              left: 0;
              bottom: 0;
              width: 200px; /* Adjust the width as needed */
              background-color: grey; /* Set the sidebar background color to green */
              overflow-y: auto; /* Enable vertical scrolling if needed */
              z-index: 1000; /* Ensure it appears above other content */
              margin:0;
              padding:0;
              transition: width 0.3s;
          }

          /* Style for submenu backgrounds */
          .sidebar-submenu {
              list-style-type: none;
              padding: 0;
              display: none; /* Hide submenus by default */
          }

          /* Updated color and font size for labels */
          #sidebar a.nav-link {
              color: white; /* Set color to black */
              font-size: 17px; /* Set font size to 25px */
              margin-top: 2px; /* Indent submenus */              
              padding-left: 20px;
          }

          .navbar-nav.sidebar-submenu li.nav-item {
            padding-left: 20px; /* Remove margin-left for submenu items */              
          }

          .navbar-nav.sidebar-submenu li.nav-item a.nav-link {
            font-size: 15px !important;/* Set font size to 14px for submenu links */
          }

          /* Hover effect for main menu items */
          .navbar-nav li.nav-item a.nav-link:hover {
              background-color: #333; /* Change background color on hover */
              color: #fff; /* Change text color on hover */
          }

          /* Hover effect for submenu links */
          .navbar-nav.sidebar-submenu li.nav-item a.nav-link:hover {
              background-color: #333; /* Change background color on hover */
              color: #fff; /* Change text color on hover */
          }


        </style>

    </head>
    <body>
        <div class="row-container">
            <!-- Side-Nav -->
            <!-- Sidebar Navigation -->
            <div class="side-navbar active-nav d-flex flex-wrap flex-column" id="sidebar">

                <ul class="navbar-nav" id="sidebar-menu-item">    
                
                <!-- Module 1: My Dashboard -->
                <li class="nav-item">
                <a href="/Dashboard" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">My Dashboard </span>
                </a>
        
                </li>
                <!-- Module 1: MyAssistant Setup -->
                <li class="nav-item">
                <a href="/setup" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Create Assistant </span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="/AskQuestion" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Ask Questions </span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="/PromptSetup" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Interview Prompts </span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="/Chat" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Answer Interview</span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="/Analyse" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Analyse Response</span>
                </a>
        
                </li>




                <li class="nav-item">
                <a href="/History" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Response History </span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="/Profile" class="nav-link h5 text-black my-2" >
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">My Profile </span>
                </a>
        
                </li>

                <li class="nav-item">
                <a href="javascript:void(0);" onclick="logout();" class="nav-link h5 text-black my-2">
                    <i class="bx bxs-dashboard"></i>
                    <span class="mx-2">Logout</span>
                </a> 
                </li>         
            </div>

        </div>
    
      
      <!-- Custom JS -->
      <script src="common.js"></script>     

  </body>
  </html>
`);
}