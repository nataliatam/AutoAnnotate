// img_path = ""
let confirm_delete = true;
var allowedExtensions = /(\.jpg|\.jpeg|\.tiff)$/i;
var badfile_warn = "**Only .jpg, .jpeg, and .tiff image files are allowed. .png image files are not allowed.**";

// implement debouncing for readImage
let readImageTimer = null;

function debouncedReadImage(event) {
    clearTimeout(readImageTimer);
    readImageTimer = setTimeout(function () {readImage(event)}, 500);
}

// function to read image as data 
function readImage(event) {
    showSpinner();
    var file = event.target.files[0];
    
    if (file) {
        var fileAllowed = allowedExtensions.exec(file.name);
        
        if (fileAllowed) {
            var reader = new FileReader();

            reader.onload = async function (e) {
                var image_data = e.target.result;
                // img_path = image_data <-- want to pass this to main.js
                try {
                    localStorage.setItem("uploadedImageData", image_data);
                } catch (err) {
                    alert("Exceeded localstorage quota (~3KB)")
                }
                // Send the image data and image name to the server
                let filename = file.name;
                sendImageToServer(image_data, filename);
            };

            reader.readAsDataURL(file);
        } else {
            var badfile_msg = file.name + " was not uploaded.";
            messagebox(badfile_msg+"<br>"+badfile_warn);
            hideSpinner();
        }
    }
}

// Function to handle image file upload on display page and then redirect
document.getElementById('image-input').addEventListener('change', function (event) {
    debouncedReadImage(event);
});

// Function to allow images with duplicate filenames to be uploaded consecutively
document.getElementById('image-input').addEventListener('click', function (event) {
    this.value = null;
});

document.getElementById('folder-input').addEventListener('change', function (event) {
    debouncedProcessFolder(event);
});

// implement debouncing for processFolder
let processFolderTimer = null;

function debouncedProcessFolder(event) {
    clearTimeout(processFolderTimer);
    processFolderTimer = setTimeout(function () {processFolder(event)}, 500);
}

function processFolder(event) {
    showSpinner();
    var folder = event.target.files;
    var num_files = folder.length;
    var currentIndex = 0;
    var bad_files = [];
    var good_files = [];

    function processFile() {
        if (currentIndex < num_files) {
            var file = folder[currentIndex];

            if (file) {
                var fileAllowed = allowedExtensions.exec(file.name);

                if (fileAllowed) {
                    var newreader = new FileReader();

                    newreader.onload = function (e) {
                        var image_data = e.target.result;
                        try {
                            localStorage.setItem("uploadedImageData", image_data);
                        } catch (err) {
                            alert("Exceeded local storage quota (~3KB)");
                        }
                        sendImageToServer(image_data, file.name, false);
                    };

                    newreader.readAsDataURL(file);
                    good_files.push(file.name);
                } else {
                    bad_files.push(file.name);
                }
                // Move to the next file after processing the current one
                currentIndex++;
                processFile();
            }
        } else { // done processing all files
            var goodfile_msg = good_files.length + " images uploaded: " + good_files;
            var badfile_msg = "The following "+bad_files.length+" files were not uploaded: " + bad_files;
            if (bad_files.length ==0) messagebox(goodfile_msg);
            else if (bad_files.length == num_files) {
                messagebox(goodfile_msg+"<br>"+badfile_msg+"<br>"+badfile_warn);
                hideSpinner();
            }
            else messagebox(goodfile_msg+"<br>"+badfile_msg+"<br>"+badfile_warn);
        }
    }
    // Start processing the first file
    processFile();
}


// Function to allow folders with duplicate filenames to be uploaded consecutively
document.getElementById('folder-input').addEventListener('click', function (event) {
    this.value = null;
})

// implement debouncing for deleteAll
let confirmDeleteTimer = null;

function debouncedConfirmDelete() {
    clearTimeout(confirmDeleteTimer);
    confirmDeleteTimer = setTimeout(confirmDelete, 500);
};

function confirmDelete() {
    if (!document.getElementById('confirm-delete').checked){
        alert("System will not double confirm before deleting an image. Toggle switch again to change this.")
    } else {
        alert("System will double confirm before deleting an image. Toggle switch again change this.")
    }
}

let setting_timeout = false
function messagebox(msg, duration="8000") {
    // code taken from: https://jsbin.com/ibUrIxu/1/edit?html,output
    // duration is in ms
    var styler = document.getElementById("messagebox");
    var s = duration / 1000;
    styler.innerHTML = "<b>"+msg+"</b><br><i>This message will disappear after "+s+" seconds.</i>";
    setting_timeout = true;
    setTimeout(function() {
        setting_timeout = false;}, 
        duration);
    setTimeout(function() {
        if (!setting_timeout) styler.innerHTML = "";}, 
        duration);
}

// Function to send image to the cloudinary and redirect to new annotation page
async function sendImageToServer(data, filename, showmessage=true) {
    // Make an AJAX request to send the image to the server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload_image', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    // Define the data to send to the server
    var imageData = JSON.stringify({data: data, image_filename : filename});
    // console.log("Preparing to send image to server");

    // Define a callback for when the request is complete
    xhr.onload = function () {
        if (xhr.status === 200) {
            // Handle success (optional)
            // console.log('Image sent to the server successfully');
            // Get the image ID from the server response
            var server_response = JSON.parse(xhr.responseText);
            var imageId = server_response.imageID; 

            // redirects
            // console.log('Server response' + server_response);
            // console.log('imageId from server to frontend' + imageId);
            if (showmessage) messagebox(filename+" saved with image ID " + imageId);
            getImageList();
        } else {
            // Handle error (optional)
            // console.error('Error sending image to the server');
                    // Extract the error message from the server response
            var errorMessage = 'An error occurred while uploading the image.';
            try {
                var response = JSON.parse(xhr.responseText);
                errorMessage = response.message || errorMessage;
            } catch (e) {
                console.error('Error parsing server response:', e);
            }

            // Show the error message to the user
            if (showmessage) {
                alert('Image Upload Error: ' + errorMessage);
            }

            // Continue with application logic (e.g., refreshing the image list)
            getImageList();
        }
    };
    // Send the image data to the server
    xhr.send(imageData);
}

document.getElementById('delete-all-button').addEventListener('click', function (event) {
    debouncedDeleteAll();
});

// implement debouncing for deleteAll
let deleteAllTimer = null;

function debouncedDeleteAll() {
    clearTimeout(deleteAllTimer);
    deleteAllTimer = setTimeout(deleteAll, 500);
};

function deleteAll() {
    confirmed = confirm("Are you sure you want to delete ALL images? This can take a while.");
    if (confirmed) {
        showDeleteSpinner();
        $.ajax({
            url: '/delete_all_images',
            type: 'GET',
            contentType: 'application/json',
            success: function(data) {
                num_images = data['num_images'];
                images_deleted = data['images_deleted'];
                console.log('Image ID(s) deleted: ' + images_deleted);
                hideDeleteSpinner();
                messagebox(num_images + " image(s) deleted from database")
                getImageList();
            },
            error: function(xhr) {
                // Extract error message from server response
                var errorMessage = 'Error deleting all images.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                alert(errorMessage);
                hideDeleteSpinner();
                getImageList();
            }
        });
    }
};

document.getElementById('export-all-button').addEventListener('click', function (event) {
    debouncedExportAll();
})

// implement debouncing for exportAll
let exportAllTimer = null;

function debouncedExportAll() {
    clearTimeout(exportAllTimer);
    exportAllTimer = setTimeout(exportAll, 500);
}

function exportAll() {
    showSpinner()
    $.ajax({
        url: '/export_all_annotations',
        type: 'GET',
        contentType: 'application/json',
        success: function(data) {
            hideSpinner();
            data = JSON.parse(data);
            annotations = data['annotations'];
            num_images = data['num_images'];
            messagebox("Exported annotations for "+num_images+" images.");
            promptDownload(annotations, filename="all_annotations.json") // TODO: edit filename to include userid after implementing multiuser stuff?
        },
        error: function(xhr) {
            hideSpinner();
            // Extract error message from server response
            var errorMessage = 'Error exporting all annotations.';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            alert(errorMessage);
        }
    });
}

function promptDownload(jsonFile, filename){
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(jsonFile));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", filename);
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  }

function track_export_buttons() {
    $.ajax({
        url: '/get_image_ids',
        type: 'GET',
        contentType: 'application/json',
        success: function(data) {
            let num_images = data['num_images'];
            let image_ids = data['image_ids'];

            for (let i = 0; i < num_images; i++) {
                let image_id = image_ids[i]
                let button_id = "export-button-"+image_id;
                let button = document.getElementById(button_id);
                if (button) {
                    button.addEventListener('click', function (event) {
                        debouncedExportAnnotation(image_id);
                    });
                }
            }
        },
        error: function(xhr) {
            // Extract error message from server response
            var errorMessage = 'Error exporting all images.';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            alert(errorMessage);
            hideDeleteSpinner();
        }
    });
}

// implement debouncing for exportAnnotation
let exportAnnotationTimer = null;

function debouncedExportAnnotation(id) {
    clearTimeout(exportAnnotationTimer);
    exportAnnotationTimer = setTimeout(function() {exportAnnotation(id)}, 500);
}

let export_request = null;

function exportAnnotation(id) {

    // Using AJAX:
    if (export_request != null)
        export_request.abort();
    let exportData = {
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'application/json' 
        },
        type: 'POST',
        url: '/export_annotations', // function in annotate.py 
        data: JSON.stringify({'id':id}),
        cache: false, // not sure what this does but Indu says we might need it
        success: function (data) { // upon success, this function will be executed
            console.log('Sent image id to server for export request'); 
            data = JSON.parse(data);
            filename = id+"_annotations.json";
            promptDownload(data, filename);
        },
        error: function (xhr) { 
            console.error('Error sending image id to server for export request');
            // Extract error message from server response
            var errorMessage = 'Error exporting annotations.';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            alert(errorMessage);
        }
    };
    export_request = $.ajax(exportData)
}

function promptDownload(jsonFile, filename){
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(jsonFile));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", filename);
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

function track_delete_buttons() {
    $.ajax({
        url: '/get_image_ids',
        type: 'GET',
        contentType: 'application/json',
        success: function(data) {
            let num_images = data['num_images'];
            let image_ids = data['image_ids'];

            for (let i = 0; i < num_images; i++) {
                let image_id = image_ids[i]
                let button_id = "delete-button-"+image_id;
                let button = document.getElementById(button_id);
                if (button) {
                    button.addEventListener('click', function (event) {
                            debouncedDeleteImage(image_id);
                    });
                }
            }
            hideSpinner()
        },
        error: function(xhr) {
            // Extract error message from server response
            var errorMessage = 'Error deleting all images.';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            alert(errorMessage);
            hideSpinner();
        }
    });
}

// implement debouncing for deleteImage
let deleteImageTimer = null;

function debouncedDeleteImage(id) {
    clearTimeout(deleteImageTimer);
    deleteImageTimer = setTimeout(function() {deleteImage(id)}, 500);
}

function deleteImage(image_id) {
    var confirmed = false;
    if (document.getElementById('confirm-delete').checked) confirmed = confirm("Are you sure you want to delete image with ID "+image_id+"?");
    if (confirmed || !document.getElementById('confirm-delete').checked) {
        showDeleteSpinner();
        console.log("deleting image with ID: "+image_id);
        $.ajax({
            url: '/delete_image?image_id='+image_id,
            type: 'GET',
            contentType: 'application/json',
            success: function() {
                hideDeleteSpinner();
                console.log('Successfully deleted image with ID = ' + image_id);
                getImageList();
            },
            error: function(xhr) {
                hideDeleteSpinner();
                // Extract error message from server response
                var errorMessage = 'Error deleting image '+image_id;
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                alert(errorMessage);
                // messagebox('Error deleting image with ID = ' + image_id);
                console.error('Error deleting image with ID = ' + image_id);
                getImageList();
            }
        });
    }
}

function showSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('cover-spin').style.display = 'block';
}

function hideSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('cover-spin').style.display = 'none';
}

function showDeleteSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('delete-spin').style.display = 'block';
}

function hideDeleteSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('delete-spin').style.display = 'none';
}


let request = null;

function getImageList () {
    showSpinner()
    let filename = encodeURIComponent($('#filenameInput').val());
    let image_id = encodeURIComponent($('#imageIdInput').val());

    // send filename and image id 
    let url = '/get_image_list?filename='+filename;
    if (image_id !== "") {
        url = url + '&image_id='+image_id;
    }
    
    if (request != null){
        // console.log("aborting request");
        request.abort();
    }

    let requestData = {
        type: 'GET',
        url: url, 
        success: function (data){
            $('#imagelist').html(data);

            // track all export and delete buttons 
            // (must be called here to ensure that buttons
            // have been generated, else element does not exist)
            track_export_buttons();
            track_delete_buttons();
            // track confirm deletion toggle
            document.getElementById("confirm-delete").checked = confirm_delete;
            document.getElementById('confirm-delete').addEventListener('change', function (event) {
                confirm_delete = !confirm_delete;
                debouncedConfirmDelete();
            });
        },
        error: function (){
            // messagebox('Error: Failed to fetch image list from server')
        }
    };

    request = $.ajax(requestData);
}

// implement debouncing for getImageList
let imageListTimer = null;

function debouncedGetImageList() {
    clearTimeout(imageListTimer);
    imageListTimer = setTimeout(getImageList, 500);
}

function setup() {
    getImageList();
    $('#filenameInput').on('input', debouncedGetImageList);
    $('#imageIdInput').on('input', debouncedGetImageList);
}

$('document').ready(setup);
