let confirm_delete = document.getElementById('confirm-delete').checked; // confirm before deleting annotation
let cat_emphasized = null;
let cat_expanded = null;
let ann_emphasized = null;
let num_kmeans_saved = 0;
let num_kmeans = null;
let unique_cat_IDs = null;
let isCancel = false;
let num_reloads_ann_cat = 0;
let max_num_reloads_ann_cat = 3;

// get references to annotation data
var x_coords = null;
var y_coords = null;
var polygon_sizes = null;
var ann_ids = null;
var colors = null;
var cat_ids = null;
var annotation_htmls = null; 
var no_annotations_html = null;
var polygon_data = null;
var annotation_id_per_cat = null;

// Get references to both canvas elements
var imageCanvas = document.getElementById('image-canvas');
var annotationCanvas = document.getElementById('annotation-canvas');
var emphasisCanvas = document.getElementById('emphasis-canvas');
var imageContext = imageCanvas.getContext('2d');
var annotationContext = annotationCanvas.getContext('2d');
var emphasisContext = emphasisCanvas.getContext('2d');
emphasisCanvas.style.zIndex = "-100";
var image_url = null;

let stored_annotation_canvas = null;
let stored_emphasis_canvas = null;
let annotation_parent = annotationCanvas.parentNode;
let emphasis_parent = emphasisCanvas.parentNode;

// var image_path = localStorage.getItem("uploadedImageData") //<-- want this from display.js

// Variable to keep track of the scale factor
var scaleFactor = 1;
var xOffSet = 0;
var yOffSet = 0;

// let points = []; // To store the coordinates of annotation points
let points_temp = []; // To temporarily store coordinates during annotation
let polygons = []; // To store user annotations in the current session
let all_polygons = []; // To store all annotations 

// Implement a local cache for annotations (optimization)
let annotationCache = [];

// Initialize category name
var category_name = null

let removePolygonMode = false;

function defaultMode() {
    // top bar
    if (colors.length == 0) {
        document.getElementById("export-button").disabled = true;
        document.getElementById("reset-button").disabled = true;
    } else {
        document.getElementById("export-button").disabled = false;
        document.getElementById("reset-button").disabled = false;
    }
    document.getElementById("delete-button").disabled = false;
    document.getElementById("return-button").disabled = false;
        
    // auto annotation
    document.getElementById("prefill-button").disabled = false;
    document.getElementById("merge-button").disabled = true;

    // manual annotation
    document.getElementById("annotate-button").disabled = false;
    document.getElementById("undo-button").disabled = true;
    document.getElementById("cancel-annotate-button").disabled = true;
    document.getElementById("end-annotate-button").disabled = true;
    if (colors.length == 0) {
        document.getElementById("remove-polygon-button").disabled = true;
    } else {
        document.getElementById("remove-polygon-button").disabled = false;
    }

    // category and annotation lists 
    disableCatAnnList(false);
}

function manualAnnotationMode(){
    // top bar
    document.getElementById("export-button").disabled = true;
    document.getElementById("reset-button").disabled = true;
    document.getElementById("delete-button").disabled = true;
    document.getElementById("return-button").disabled = true;
        
    // auto annotation
    document.getElementById("prefill-button").disabled = true;
    document.getElementById("merge-button").disabled = true;

    // manual annotation
    document.getElementById("annotate-button").disabled = true;
    document.getElementById("cancel-annotate-button").disabled = false;
    document.getElementById("remove-polygon-button").disabled = true;

    // manual annotation buttons dependent on number of points drawn 
    if (points_temp.length >= 3) document.getElementById("end-annotate-button").disabled = false;
    else document.getElementById("end-annotate-button").disabled = true;
    if (points_temp.length >= 1) document.getElementById("undo-button").disabled = false;
    else document.getElementById("undo-button").disabled = true;

    // category and annotation lists 
    disableCatAnnList(true);
}

function autoAnnotationMode(){
    // top bar
    document.getElementById("export-button").disabled = true;
    document.getElementById("reset-button").disabled = true;
    document.getElementById("delete-button").disabled = true;
    document.getElementById("return-button").disabled = true;
        
    // auto annotation
    document.getElementById("prefill-button").disabled = true;
    document.getElementById("merge-button").disabled = false;

    // manual annotation
    document.getElementById("annotate-button").disabled = true;
    document.getElementById("undo-button").disabled = true; 
    document.getElementById("cancel-annotate-button").disabled = true;
    document.getElementById("end-annotate-button").disabled = true; 
    document.getElementById("remove-polygon-button").disabled = true;

    // category and annotation lists 
    disableCatAnnList(true);
}

function deleteAnnMode() {
    // top bar
    document.getElementById("export-button").disabled = true;
    document.getElementById("reset-button").disabled = true;
    document.getElementById("delete-button").disabled = true;
    document.getElementById("return-button").disabled = true;
        
    // auto annotation
    document.getElementById("prefill-button").disabled = true;
    document.getElementById("merge-button").disabled = true;

    // manual annotation
    document.getElementById("annotate-button").disabled = true;
    document.getElementById("undo-button").disabled = true; 
    document.getElementById("cancel-annotate-button").disabled = true;
    document.getElementById("end-annotate-button").disabled = true; 
    document.getElementById("remove-polygon-button").disabled = false;

    // category and annotation lists 
    disableCatAnnList(true);
}

function disableCatAnnList(disable) {
    for (let i = 0; i < unique_cat_IDs.length; i++) {
        document.getElementById("emphasize-button-"+unique_cat_IDs[i]).disabled = disable;
    }
    if (cat_expanded) {
        ann_ids = annotation_id_per_cat[cat_expanded];
        for (let i = 0; i < ann_ids.length; i++) {
            // button = document.getElementById("emphasize-ann-button-"+ann_ids[i])
            // if (button) button.disabled = disable;
            document.getElementById("emphasize-ann-button-"+ann_ids[i]).disabled = disable;
        }
    }
}
// --------------------------------------------------------------------------------------------
// --------------------------------------------------------------------------------------------
// UPLOAD

// Function to load image onto canvas
function displayImage() {
    showSpinner();

    // Create an Image object
    var img = new Image();
    img.onload = function () {
        var canvasWidth = imageCanvas.width;
        var canvasHeight = imageCanvas.height;
        var imageWidth = img.width;
        var imageHeight = img.height;

        // Calculate the scaling factors
        var scaleWidth = canvasWidth / imageWidth;
        var scaleHeight = canvasHeight / imageHeight;
        var scale = Math.min(scaleWidth, scaleHeight);

        // Update the scale factor
        scaleFactor = scale;

        // Calculate the new dimensions for the scaled image
        var newWidth = imageWidth * scale;
        var newHeight = imageHeight * scale;
        xOffSet = (canvasWidth - newWidth) / 2
        yOffSet = (canvasHeight -  newHeight) / 2

        // Log the scaled image width and height
        // console.log('Scaled Image Width:', newWidth);
        // console.log('Scaled Image Height:', newHeight);

        // Calculate the position to center the image on the canvas
        var x = (canvasWidth - newWidth) / 2;
        var y = (canvasHeight - newHeight) / 2;

        // Clear the canvas and draw the scaled image
        imageContext.clearRect(0, 0, canvasWidth, canvasHeight);
        imageContext.drawImage(img, x, y, newWidth, newHeight);
    };
    
    // Load the image
    image_path = image_url;
    img.src = image_url;
    hideSpinner();
}

// Function to draw annotations loaded from db
function drawAnnotations(categories_html) {
    $('#categories').html(categories_html); 
    unique_cat_IDs = new Set(cat_ids)
    unique_cat_IDs = [...unique_cat_IDs];
    track_emphasize_buttons(unique_cat_IDs);
    track_delete_cat_buttons(unique_cat_IDs);
    track_show_ann_buttons(unique_cat_IDs);

    let num_polygons = colors.length;

    defaultMode();

    let coords_loaded_points = 0;
    let coords_loaded_lines = 0;

    let points_temp = [];

    // set transparency
    annotationContext.globalAlpha = 0.4

    // draw and color each polygon 
    for (let polygon_num = 0; polygon_num < num_polygons; polygon_num++) {
        let r = colors[polygon_num][0];
        let g = colors[polygon_num][1];
        let b = colors[polygon_num][2];
        let size = polygon_sizes[polygon_num];
        let color = "rgb("+r+", "+g+", "+b+")";

        // draw the points
        for (let point_num = 0; point_num < size; point_num++) {
            annotationContext.fillStyle = color; 
            annotationContext.beginPath();
            // scale down polygons
            let x = x_coords[coords_loaded_points]/scaleFactor
            let y = y_coords[coords_loaded_points]/scaleFactor
            annotationContext.arc(x, y, 3, 0, Math.PI * 2, true);
            coords_loaded_points = coords_loaded_points + 1;  
        }
        annotationContext.fill();

        // connect the points
        annotationContext.strokeStyle = color; // Set the polygon line color
        annotationContext.lineWidth = 2; // Set the polygon line width
        annotationContext.beginPath();
        
        // connect points in this polygon 
        for (let point_num = 0; point_num < size; point_num++) {
            // scale down polygons
            let x = x_coords[coords_loaded_lines]/scaleFactor;
            let y = y_coords[coords_loaded_lines]/scaleFactor;
            points_temp.push({ x, y });

            annotationContext.arc(x, y, 3, 0, Math.PI * 2, true);
            coords_loaded_lines = coords_loaded_lines + 1;

            if (point_num == 0) { 
                // console.log("line starting from point ("+x+", "+y+")")
                annotationContext.moveTo(x, y);
            } else {
                // console.log("line connecting to point ("+x+", "+y+")")
                annotationContext.lineTo(x, y);
            }        
        }
        // Check for duplicated points
        let isDuplicate = false;
        for (let tempPoint of points_temp) {
            if (isPointInAllPolygons(tempPoint, all_polygons)) {
                isDuplicate = true;
                break;
            }
        }

        // Push points_temp to all_polygon if no duplicates
        if (!isDuplicate) {
            all_polygons.push({ points: points_temp, annotationId: ann_ids[polygon_num] });
            annotationCache = all_polygons; // TEST: FOR UNDO
        }
        points_temp = [];

        annotationContext.fill();
        annotationContext.closePath();
        annotationContext.stroke();
    }
    console.log("all_polygons: ", all_polygons);
    /* For debugging
    all_polygons.forEach(polygon => {
        const { points, annotationId } = polygon; // Destructuring to get properties
        console.log('Polygon Points:', points);
        console.log('Annotation ID:', annotationId);
    });
    */
   hideSpinner();
}

// Function to load existing annotations and categories
function loadAnnCat(callback) {
    showSpinner();
    image_id = getImageID();

    console.log("Retrieving existing annotations from server");
    let url = '/load_annotations?image_id='+image_id;

    let requestData = {
        type: 'GET',
        url: url, 
        success: function (data) {
            cat_expanded = false;
            categories_html = data['categories_html'];
            cat_ids = data['cat_IDs'];
            var annotation_data = data['annotation_data'];
            annotation_htmls = data['annotation_htmls'];
            no_annotations_html = data['no_annotations_html'];
            polygon_data = data['polygon_data'];
            annotation_id_per_cat = data['annotation_id_per_cat'];

            x_coords = annotation_data["x_coords"];
            y_coords = annotation_data["y_coords"];
            polygon_sizes = annotation_data["polygon_sizes"]; // used to see how many x, y coordinates to read per polygon
            ann_ids = annotation_data["ann_ids"] // a list of annotation ids
            colors = annotation_data["colors"];

            drawAnnotations(categories_html);
            callback();
        },
        error: function (xhr){
            // Extract error message from server response
            var errorMessage = 'Error deleting image '+image_id;
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }            
            if (num_reloads_ann_cat == max_num_reloads_ann_cat) {
                num_reloads_ann_cat = 0;
                alert(errorMessage + " after "+max_num_reloads_ann_cat+" retries, try refreshing the page again or contact system administrator.");
            } else {
                messagebox(errorMessage + ", retrying...");
                num_reloads_ann_cat+=1;
                loadAnnCat();
            }
            console.log('Error: Failed to fetch existing annotations');
            hideSpinner();
        }
    };

    $.ajax(requestData);
}

// Function to show categories 
let request = null;

function track_delete_cat_buttons(unique_cat_IDs) {
    for (let i = 0; i < unique_cat_IDs.length; i++) {
        let cat_id = unique_cat_IDs[i];
        let button_id = "delete-cat-button-"+cat_id;
        // console.log("tracking: "+button_id);
        let button = document.getElementById(button_id);
        button.className = "fa fa-trash-o";
        if (button) {
            button.addEventListener('click', function (event) {
                debouncedDelete(cat_id);
            });
        }
    }
}

// implement debouncing for trackDelete
let deleteTimer = null;

function debouncedDelete(cat_id) {
    clearTimeout(deleteTimer);
    deleteTimer = setTimeout(function() {
        trackDelete(cat_id);}, 500);
};

function trackDelete(cat_id){
    if (confirm_delete) {
        confirmed = confirm("Are you sure you want to delete all annotations under the category with ID "+cat_id+" in this image?");
        if (confirmed) deleteCategory(cat_id);
    } else {
        console.log("deleting category with ID: "+cat_id);
        deleteCategory(cat_id);
    }
}

function track_show_ann_buttons(unique_cat_IDs) {
    let annlist = document.getElementById("annotations");
    $(annlist).html(no_annotations_html); 

    for (let i = 0; i < unique_cat_IDs.length; i++) {
        let cat_id = unique_cat_IDs[i];
        let button_id = "show-ann-button-"+cat_id;
        let button = document.getElementById(button_id);
        button.className = "fa fa-plus";
        if (button) {
            button.addEventListener('click', function (event) {
                debouncedShowAnn(button,cat_id,unique_cat_IDs,annlist);
            });
        }
    }
}

// implement debouncing for trackDelete
let showAnnTimer = null;

function debouncedShowAnn(button,cat_id,unique_cat_IDs,annlist) {
    clearTimeout(showAnnTimer);
    showAnnTimer = setTimeout(function() {
        showAnn(button,cat_id,unique_cat_IDs,annlist);}, 500);
};

function showAnn(button,cat_id,unique_cat_IDs,annlist){
    if (cat_expanded == null) { // not currently showing any annotations
        alert("Hide the annotations for this category by clicking this button again. You can only show the annotations for one category at a time.")
        button.className = "fa fa-minus";
        $(annlist).html(annotation_htmls[cat_id]); 
        cat_expanded = cat_id;
        track_emphasize_ann_button(unique_cat_IDs, annotation_id_per_cat[cat_id])
        track_delete_ann_button(annotation_id_per_cat[cat_id])
        close_cat_button = document.getElementById("close-cat-button");
        close_cat_button.addEventListener('click', function (event) {
            debouncedCloseCat();
        });

        // implement debouncing for track_emphasis
        let closeCatTimer = null;

        function debouncedCloseCat() {
            clearTimeout(closeCatTimer);
            closeCatTimer = setTimeout(closeCat, 500);
        };

        function closeCat() {
            $(annlist).html(no_annotations_html);
            button.className = "fa fa-plus";
            for (let j = 0; j < unique_cat_IDs.length; j++) {
                if (cat_id != unique_cat_IDs[j]) {
                    document.getElementById("show-ann-button-"+unique_cat_IDs[j]).disabled = false;
                }
            }
        }

        for (let j = 0; j < unique_cat_IDs.length; j++) {
            if (cat_id != unique_cat_IDs[j]) {
                document.getElementById("show-ann-button-"+unique_cat_IDs[j]).disabled = true;
            }
        }
    } else { // already showing annotations for this category
        button.className = "fa fa-plus";
        $(annlist).html(no_annotations_html); 
        cat_expanded = null;
        for (let j = 0; j < unique_cat_IDs.length; j++) {
            if (cat_id != unique_cat_IDs[j]) {
                document.getElementById("show-ann-button-"+unique_cat_IDs[j]).disabled = false;
            }
        }
    }
}

function track_emphasize_ann_button(unique_cat_IDs, ann_ids) {
    for (let i = 0; i < ann_ids.length; i++) {
        let ann_id = ann_ids[i];
        let button_id = "emphasize-ann-button-"+ann_id;
        let button = document.getElementById(button_id);
        button.className = "fa fa-eye";
        if (cat_emphasized || removePolygonMode) button.disabled = true;
        if (button) {
            button.addEventListener('click', function () {
                debouncedEmphasizeAnn(button, ann_id, unique_cat_IDs);
            });
        }
    }
}
// implement debouncing for emphasizeAnn
let emphasizeAnnTimer = null;

function debouncedEmphasizeAnn(button, ann_id, unique_cat_IDs) {
    clearTimeout(emphasizeAnnTimer);
    emphasizeAnnTimer = setTimeout(function() {
        emphasizeAnn(button, ann_id, unique_cat_IDs);}, 500);
};

function emphasizeAnn(button, ann_id, unique_cat_IDs) {
    if (ann_emphasized == null ) { // not currently emphasizing anything
        alert("Un-highlight this annotation by clicking this button again. You can only highlight one annotation at a time.")
        button.className = "fa fa-eye-slash";
        drawAnnEmphasis(ann_id);
        ann_emphasized = ann_id;
        for (let j = 0; j < ann_ids.length; j++) {
            if (ann_id != ann_ids[j]) document.getElementById("emphasize-ann-button-"+ann_ids[j]).disabled=true;
        }
        for (let j = 0; j < unique_cat_IDs.length; j++) {
            document.getElementById("emphasize-button-"+unique_cat_IDs[j]).disabled=true;
        }
    } else if (ann_emphasized == ann_id) { // already emphasizing this category
        button.className = "fa fa-eye";
        clearEmphasis();
        ann_emphasized = null;
        for (let j = 0; j < ann_ids.length; j++) {
            if (ann_id != ann_ids[j]) document.getElementById("emphasize-ann-button-"+ann_ids[j]).disabled=false;
        }
        for (let j = 0; j < unique_cat_IDs.length; j++) {
            document.getElementById("emphasize-button-"+unique_cat_IDs[j]).disabled=false;
        }
    }
}

function clearEmphasis() {
    emphasisContext.clearRect(0, 0, emphasisCanvas.width, emphasisCanvas.height);
    emphasisCanvas.style.zIndex = "-100";
    ann_emphasized = null;
    cat_emphasized = null;
}

function track_delete_ann_button(ann_ids) {
    for (let i = 0; i < ann_ids.length; i++) {
        let ann_id = ann_ids[i];
        let button_id = "delete-ann-button-"+ann_id;
        let button = document.getElementById(button_id);
        button.className = "fa fa-trash-o";
        if (button) {
            button.addEventListener('click', function (event) {
                debouncedDeleteAnn(ann_id);});
        }
    }
}

// implement debouncing for deleteAnn
let deleteAnnTimer = null;

function debouncedDeleteAnn(ann_id) {
    clearTimeout(deleteAnnTimer);
    deleteAnnTimer = setTimeout(function() {
        deleteAnn(ann_id);}, 500);
};

function deleteAnn(ann_id){
    if (confirm_delete) {
        confirmed = confirm("Are you sure you want to delete annotation with ID "+ann_id+" in this image?");
        if (confirmed) deleteAnnotation(ann_id, function() {
            redrawAnnotationCanvas(defaultMode); // Redraw the canvas here
        });
    } else {
        console.log("Deleting annotation with ID: "+ann_id);
        if (confirmed) deleteAnnotation(ann_id, function() {
            redrawAnnotationCanvas(defaultMode); // Redraw the canvas here
        });
    }
};

// Function to draw all given annotations with emphasis 
function drawAnnEmphasis(ann_id) {
    emphasisCanvas.style.zIndex = "100";

    let x_coords = polygon_data["x_coords"][ann_id];
    let y_coords = polygon_data["y_coords"][ann_id];
    let polygon_size = polygon_data["polygon_sizes"][ann_id]; // used to see how many x, y coordinates to read per polygon
    let color = "black";

    // draw the points
    for (let i = 0; i < polygon_size; i++) {
        emphasisContext.beginPath();
        emphasisContext.fillStyle = color;
        // scale down polygons
        let x = x_coords[i]/scaleFactor
        let y = y_coords[i]/scaleFactor
        emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);
    }
    emphasisContext.strokeStyle = color; // Set the polygon line color
    emphasisContext.lineWidth = 5; // Set the polygon line width
    emphasisContext.beginPath();
        
    // connect points in this polygon 
    for (let i = 0; i < polygon_size; i++) {
        // scale down polygons
        let x = x_coords[i]/scaleFactor;
        let y = y_coords[i]/scaleFactor;
        console.log("x,y: " +x+", "+y);

        emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);

        if (i == 0) { 
            emphasisContext.moveTo(x, y);
        } else {
            emphasisContext.lineTo(x, y);
        }   
    }
    let x = x_coords[0]/scaleFactor;
    let y = y_coords[0]/scaleFactor;
    emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);
    emphasisContext.lineTo(x, y); // final line
    emphasisContext.stroke();
    emphasisContext.closePath();
    flashEmphasis();
}

function track_emphasize_buttons(unique_cat_IDs) {
    for (let i = 0; i < unique_cat_IDs.length; i++) {
        let cat_id = unique_cat_IDs[i];
        let button_id = "emphasize-button-"+cat_id;
        let button = document.getElementById(button_id);
        button.className = "fa fa-eye";
        if (button) {
            button.addEventListener('click', function () {
                debouncedTrackEmphasis(button, cat_id, unique_cat_IDs);
            });
        }
    }
}

// implement debouncing for track_emphasis
let emphasisTimer = null;

function debouncedTrackEmphasis(button, cat_id, unique_cat_IDs) {
    clearTimeout(emphasisTimer);
    emphasisTimer = setTimeout(function() {
        trackEmphasis(button, cat_id, unique_cat_IDs);}, 500);
};

function trackEmphasis(button, cat_id, unique_cat_IDs) {
    if (cat_emphasized == null ) { // not currently emphasizing anything
        button.className = "fa fa-eye-slash";
        alert("Un-highlight this category by clicking this button again. You can only highlight one category at a time.")
        drawEmphasis(cat_id);
        cat_emphasized = cat_id;
        for (let j = 0; j < unique_cat_IDs.length; j++) {
            if (cat_id != unique_cat_IDs[j]) {
                document.getElementById("emphasize-button-"+unique_cat_IDs[j]).disabled = true;
            }
        }
        if (cat_expanded) {
            ann_ids = annotation_id_per_cat[cat_expanded];
            for (let j = 0; j < ann_ids.length; j++) {
                document.getElementById("emphasize-ann-button-"+ann_ids[j]).disabled = true;
            }
        }
    } else if (cat_emphasized == cat_id) { // already emphasizing this category
        button.className = "fa fa-eye";
        // clear the emphasis  
        emphasisContext.clearRect(0, 0, emphasisCanvas.width, emphasisCanvas.height);
        emphasisCanvas.style.zIndex = "-100";
        cat_emphasized = null;

        for (let j = 0; j < unique_cat_IDs.length; j++) {
            if (cat_id != unique_cat_IDs[j]) {
                document.getElementById("emphasize-button-"+unique_cat_IDs[j]).disabled = false;
            }
        }
        if (cat_expanded) {
            ann_ids = annotation_id_per_cat[cat_expanded];
            for (let j = 0; j < ann_ids.length; j++) {
                document.getElementById("emphasize-ann-button-"+ann_ids[j]).disabled = false;
            }
        }
    } 
}

// Function to draw all given annotations with emphasis 
function drawEmphasis(cat_id) {
    emphasisCanvas.style.zIndex = "100";

    let num_polygons = cat_ids.length;
    let coords_loaded_points = 0;
    let coords_loaded_lines = 0;
    let draw = false;
    let color = "black";

    // set transparency
    emphasisContext.globalAlpha = 0.8

    // draw and color each polygon 
    for (let polygon_num = 0; polygon_num < num_polygons; polygon_num++) {
        // console.log("cat_ids[polygon_num]: "+cat_ids[polygon_num]);
        // console.log("cat_id: "+cat_id);
        if (cat_ids[polygon_num] == cat_id){
            draw = true;
        }

        // console.log("cat_ids[polygon_num]: "+cat_ids[polygon_num]);
        // console.log("cat_id: "+cat_id);
        let size = polygon_sizes[polygon_num];
       
        // draw the points
        for (let point_num = 0; point_num < size; point_num++) {
            if (draw) {
                emphasisContext.beginPath();
                emphasisContext.fillStyle = color;
                // scale down polygons
                let x = x_coords[coords_loaded_points]/scaleFactor
                let y = y_coords[coords_loaded_points]/scaleFactor
                emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);
            }
            coords_loaded_points = coords_loaded_points + 1;  
        }
        if (draw) { // connect the points
            emphasisContext.strokeStyle = color; // Set the polygon line color
            emphasisContext.lineWidth = 5; // Set the polygon line width
            emphasisContext.beginPath();
        }
        
        // connect points in this polygon     
        for (let point_num = 0; point_num < size; point_num++) {
            // scale down polygons
            if (draw) {
                let x = x_coords[coords_loaded_lines]/scaleFactor;
                let y = y_coords[coords_loaded_lines]/scaleFactor;

                emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);

                if (point_num == 0) { 
                    // console.log("line starting from point ("+x+", "+y+")")
                    emphasisContext.moveTo(x, y);
                } else {
                    // console.log("line connecting to point ("+x+", "+y+")")
                    emphasisContext.lineTo(x, y);
                }   
            }
            coords_loaded_lines = coords_loaded_lines + 1;
        }
        if (draw) {
            let x = x_coords[coords_loaded_lines-size]/scaleFactor;
            let y = y_coords[coords_loaded_lines-size]/scaleFactor;
            emphasisContext.arc(x, y, 3, 0, Math.PI * 2, true);
            emphasisContext.lineTo(x, y); // final line
            emphasisContext.stroke();
            emphasisContext.closePath();
        }
        draw = false;
    }
    flashEmphasis();
}

// function to delete all annotations in a category for an image
function deleteCategory(cat_id) {
    const data = { category_id : cat_id, image_id : getImageID()};

    fetch('/delete_category', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            // If the response is not OK, throw an error with the response's JSON data
            return response.json().then(data => {
                throw new Error(data.message || "Unknown error occurred");
            });
        }
        return response.json();
    })
    .then(data => {
        clearEmphasis();
        console.log('Success:', data);
        redrawAnnotationCanvas(defaultMode);
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("Please contact system admin.: "+ error);
    });
}

// Alert that deleting will no longer be double-confirmed 
document.getElementById('confirm-delete').addEventListener('change', function (event) {
    debouncedConfirmDelete();
});

// implement debouncing for deleteAll
let confirmDeleteTimer = null;

function debouncedConfirmDelete() {
    clearTimeout(confirmDeleteTimer);
    confirmDeleteTimer = setTimeout(confirmDelete, 500);
};

function confirmDelete() {
    confirm_delete = document.getElementById('confirm-delete').checked; 
    if (!confirm_delete){
        alert("System will not double confirm before deleting an annotation. Toggle switch again to change this.")
    } else {
        alert("System will double confirm before deleting an annotation. Toggle switch again to change this.")
    }
}

// Helper functions
function isPointInAllPolygons(point, all_polygons) {
    for (let polygon of all_polygons) {
        for (let existingPoint of polygon.points) {
            if (existingPoint.x === point.x && existingPoint.y === point.y) {
                return true;
            }
        }
    }
    return false;
}

// --------------------------------------------------------------------------------------------
// ANNOTATE

let isAnnotationMode = false; // A flag to indicate if annotation mode is active

// Function to handle the start of annotation
function startAnnotation() {
    isAnnotationMode = true;
    manualAnnotationMode();
    points_temp = [];
    annotationCanvas.style.cursor = 'crosshair';
}

// get image id of current displaying image 
function getImageID() {
    // get the appropriate image id for current image 
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('image_id'); 
}

// get image url of current displaying image 
function loadImage() {
    // get the appropriate image id for current image <-- UNSAFE implementation 
    // const urlParams = new URLSearchParams(window.location.search);
    // return urlParams.get('image_url'); 
    let requestData = {
        type: 'GET',
        url: '/get_image_url?image_id='+getImageID(), 
        success: function (data) {
            // console.log("data: "+data);
            data = JSON.parse(data);
            // console.log("data: "+data);
            if (data['image_found']) {
                console.log("data['image_url']: "+data['image_url']);
                image_url = data['image_url'];
                displayImage();
            } else {
                loadImage();
                alert(data['message']);
                window.location.href = '/';
            }
        }
    };
    $.ajax(requestData);
}

// Cancel current annotation 
document.getElementById('cancel-annotate-button').addEventListener('click', function (event) {
    debouncedCancelAnnotate();
});

// implement debouncing for deleteAll
let cancelAnnotateTimer = null;

function debouncedCancelAnnotate() {
    clearTimeout(cancelAnnotateTimer);
    cancelAnnotateTimer = setTimeout(cancelAnnotation, 500);
};

function cancelAnnotation() {
    var confirmed = confirm("Are you sure you want to cancel and discard your current annotation? This action cannot be undone.");
    if (confirmed) {
        points_temp = [];
        isCancel = true;
        endAnnotation();
    }
}

// Function to handle the end of annotation
function endAnnotation() {
    isAnnotationMode = false;
    if (removePolygonMode == true) {
        annotationCanvas.style.cursor = 'crosshair';
    }
    else {
        annotationCanvas.style.cursor = 'auto';
    }

    // Draw the final polygon only if there are at least three points in points_temp
    if (points_temp.length >= 3) {
        // Draw the polygon
        drawPolygon(points_temp);

        // Image id
        const image_id = getImageID();

        // Send the annotation data to the server
        const annotationData = JSON.stringify({ 
            // Other than the segmentation coordinates, 
            // all values are generated randomly for prototype testing
            new_image_id: image_id, // TODO: should be loaded from page URL
            new_category_name: category_name, // user must choose category ID before annotation (window prompt)
            seg_coords: points_temp,
            bound_coords: [(5,6),(7,8)], 
            new_area: 4, 
            new_iscrowd: true,
            new_isbbox: true, 
            new_color: true
            // TODO: Generate the correct values for these data
        });
        sendAnnotationDataToServer(annotationData, function(annotation_id) {
            // This code will execute after the AJAX request completes
            polygons.push({ points: points_temp, annotationId: annotation_id }); // Maintain user annotations in current sess
            all_polygons.push({ points: points_temp, annotationId: annotation_id }); // Maintain all annotations

            points_temp = [];

            // Clear the canvas and redraw existing points and polygons
            redrawCanvas();
        });
    } else { 
        // If there are fewer than three points in points_temp, clear points_temp
        points_temp = [];
        if (!isCancel) alert("No annotations were drawn because you need more than 2 points.")
        // Clear the canvas and redraw existing points and polygons
        isCancel = false;
        redrawCanvas();
    }
}

// Function to redraw existing points and polygons on the canvas
// function loadAndredrawCanvas()
function redrawCanvas() {
    // Clear the canvas
    annotationContext.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);
    // loadImage();
    loadAnnCat(defaultMode); // TBD: Need to optimize, do not load from db everytime we redraw canvas
    annotationCache = all_polygons; // Update annotation cache
}

// Function to draw a polygon on the canvas
function drawPolygon(polygonPoints) {
    annotationContext.strokeStyle = 'red'; // Set the polygon line color
    annotationContext.lineWidth = 2; // Set the polygon line width
    annotationContext.beginPath();
    annotationContext.moveTo(polygonPoints[0].x, polygonPoints[0].y);

    for (let i = 1; i < polygonPoints.length; i++) {
        annotationContext.lineTo(polygonPoints[i].x, polygonPoints[i].y);
    }

    annotationContext.closePath();
    annotationContext.stroke();
}

// Function to draw a point on the canvas
function drawPoint(point) {
    annotationContext.fillStyle = 'red'; // Set the dot color
    annotationContext.beginPath();
    annotationContext.arc(point.x, point.y, 3, 0, Math.PI * 2, true);
    annotationContext.fill();
}

let message = null;

// Function to send annotation data to the server
function sendAnnotationDataToServer(annotationData, callback) {
    const scaledAnnotationData = JSON.parse(annotationData);
    console.log("annotationData ", annotationData)
    console.log("scaledAnnotationData ", scaledAnnotationData)
    scaledAnnotationData.seg_coords = scaledAnnotationData.seg_coords.map(
        point => ({ x: point.x * scaleFactor, y: point.y * scaleFactor })
    );

    console.log("Sending Annotation Data to Server:", scaledAnnotationData);

    $.ajax({
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        type: 'POST',
        url: '/save_annotations',
        data: JSON.stringify(scaledAnnotationData),
        cache: false,
        success: function (response) {
            console.log('Response from Server:', response);
            if (response.hasOwnProperty('annotationId') && response.annotationId >= 0) {
                callback(response.annotationId);
            } else {
                // Display error message to the user
                alert('Error: ' + (response.message || 'Failed to save annotation. No annotation ID returned from server.'));
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log('Error saving annotation data:', textStatus, errorThrown);
            // Extract error message
            var errorMessage = jqXHR.responseJSON && jqXHR.responseJSON.error ? jqXHR.responseJSON.error : textStatus;
            alert('Error saving annotation data: ' + errorMessage);
        }
    });
}

// Event listener for the "End Annotation" button
document.getElementById('end-annotate-button').addEventListener('click', function () {
    debouncedEndAnnotate();
});

// implement debouncing for endAnnotate
let endAnnotateTimer = null;

function debouncedEndAnnotate() {
    clearTimeout(endAnnotateTimer);
    endAnnotateTimer = setTimeout(endAnnotate, 500);
};

function endAnnotate(){
        defaultMode();
        endAnnotation();
}

// Event listener for the "Delete image and all associated data" button
document.getElementById('delete-button').addEventListener('click', function () {
    debouncedDeleteImage();
});

// implement debouncing for deleteImage
let deleteImageTimer = null;

function debouncedDeleteImage() {
    clearTimeout(deleteImageTimer);
    deleteImageTimer = setTimeout(deleteImage, 500);
};

function deleteImage(){
    const userConfirmed = confirm("Are you sure you want to delete this image and all associated annotations? This action cannot be undone.");

    if (userConfirmed) {
        image_id = getImageID();
        console.log("deleting: image ID = "+image_id);

        let url = '/delete_image?image_id='+image_id;

        let requestData = {
            type: 'GET',
            url: url, 
            success: function () {
                console.log("Deleted image with ID "+image_id+" and all associated data.");
                window.location.href = '/';
            },
            error: function (xhr){
                // Extract error message from server response
                var errorMessage = 'Error deleting image '+image_id;
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                alert(errorMessage);
                console.error('Error deleting image with ID = ' + image_id);
                //alert('Error: Failed to delete image with ID '+image_id);
                window.location.href = '/';
            }
        };
        $.ajax(requestData);
    }
}
let mergeAttemped = false;

annotationCanvas.addEventListener('mousedown', function (event) {
    if (isAnnotationMode) {
        console.log("mousedown detected in annotation mode");
        const rect = annotationCanvas.getBoundingClientRect();
        const scaleX = annotationCanvas.width / rect.width;    // Scaling factor for X
        const scaleY = annotationCanvas.height / rect.height;  // Scaling factor for Y

        const x = (event.clientX - rect.left) * scaleX;  // Adjusted X position
        const y = (event.clientY - rect.top) * scaleY;   // Adjusted Y position
        const point = { x, y };
        // console.log(point)

        // Draw the annotation dot
        drawPoint(point);

        // Store the point in points_temp
        points_temp.push(point);
        manualAnnotationMode();
    } else if (isMergingMode) {
        mergeAttemped = true;
        var rect = annotationCanvas.getBoundingClientRect();
        var x = event.clientX - rect.left;
        var y = event.clientY - rect.top;
        let click = {'click_x' : x, 'click_y' : y};
        console.log(click);
        x = (x-xOffSet)/scaleFactor;  // Adjusted X position
        y = (y-yOffSet)/scaleFactor;  // Adjusted Y position
        let point = { 'x': x, 'y': y };
        console.log(point)

        removeIndex = getIndexOfRemovedPixel(point, suppixel_coords)
        kmeans_labels[removeIndex] = -1
        // TODO: how to implement color change of polygon
    }
});

// Event listener for the "Annotate" button
document.getElementById('annotate-button').addEventListener('click', function () {
    debouncedAnnotate();
});

// implement debouncing for annotate
let annotateTimer = null;

function debouncedAnnotate() {
    clearTimeout(annotateTimer);
    annotateTimer = setTimeout(annotate, 500);
};

function annotate(){
    if (removePolygonMode == true) {
        alert("Invalid Action. You must disable remove annotations first.")
        endAnnotation();
        annotationCanvas.style.cursor = 'crosshair';
    }
    else {
        manualAnnotationMode();

        category_name = prompt("Enter category name", "None")
        if (category_name == null) {
            defaultMode();
        }
        if (!isAnnotationMode && (category_name!==null)) {
            startAnnotation();
        }
    }
}

// --------------------------------------------------------------------------------------------
// UNDO

// Event listener for the "Undo" button
document.getElementById('undo-button').addEventListener('click', function () {
    debouncedUndo();
});

// implement debouncing for undo
let undoTimer = null;

function debouncedUndo() {
    clearTimeout(undoTimer);
    undoTimer = setTimeout(undo, 500);
};

function undo(){
    if (isMergingMode) {
        alert("Invalid Action. You must merge prefilled annotations first.");
    }
    else{
        undoAnnotation();
    }
}

// Add keydown event listener for handling Ctrl/Cmd-Z shortcut
document.addEventListener('keydown', function (event) {
    // Check if Ctrl or Cmd key is pressed along with the Z key
    if ((event.ctrlKey || event.metaKey) && event.key === 'z') {
        undoAnnotation();
    }
});

// Function to handle undoing annotation actions
function undoAnnotation() {
    if (isAnnotationMode) {
        // Undo the last annotation point
        points_temp.pop();
        manualAnnotationMode();
        redrawAnnotationCanvas(manualAnnotationMode); // Redraw all polygons
    }
}

// Function to redraw the annotation canvas after undoing a point
function redrawAnnotationCanvas(callback) {
    // Clear the annotation canvas
    annotationContext.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);

    // Set the style for the points
    annotationContext.fillStyle = 'red';

    // Redraw the annotation points in the current session
    for (const point of points_temp) {
        annotationContext.beginPath();
        annotationContext.arc(point.x, point.y, 3, 0, Math.PI * 2, true); // Draw a circle for each point
        annotationContext.fill(); // Fill the circle
    }

    // loadImage();
    loadAnnCat(callback); // TODO TBD: Need to optimize, do not load from db everytime we redraw canvas
}

// --------------------------------------------------------------------------------------------
// RETURN

// Event listener for the "Return to dashboard" button
document.getElementById('return-button').addEventListener('click', function () {
    debouncedReturn();
});

// implement debouncing for exportAnn
let returnTimer = null;

function debouncedReturn() {
    clearTimeout(returnTimer);
    returnTimer = setTimeout(returnBut, 500);
};

function returnBut(){
    window.location.href = '/';
}

// --------------------------------------------------------------------------------------------
// RESET

// Event listener for the "Reset" button
document.getElementById('reset-button').addEventListener('click', debouncedReset);

// implement debouncing for exportAnn
let resetTimer = null;

function debouncedReset() {
    clearTimeout(resetTimer);
    resetTimer = setTimeout(reset, 500);
};

function reset() {
    const imageId = getImageID();
    // Confirmation prompt
    const userConfirmed = confirm("Are you sure you want to delete all annotations for this image? This action cannot be undone.");

    if (userConfirmed) {
        // User clicked "OK", proceed with deletion
        fetch('/delete-all-annotations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_id: imageId }),
        })
        .then(response => {
            if (!response.ok) {
                // If the response is not OK, throw an error with the response's JSON data
                return response.json().then(data => {
                    throw new Error(data.message || "Unknown error occurred");
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data.message);
            // Clear the canvas
            resetCanvas();
        })
        .catch((error) => {
            console.error('Error:', error);
            alert("Error deleting all annotations. Please contact system admin. " + error);
            resetCanvas();
        });
    } else {
        // User clicked "Cancel", do nothing
        console.log("Deletion cancelled by the user.");
    }
}

// Function to reset the canvas (remove all annotations and polygons)
// TBD: Reset should remove all user-annotated and k-means annotations from db
// Reset should prompt user to confirm if they want to proceed (safety measure)
function resetCanvas() {
    // Clear the polygons array
    all_polygons = [];
    // Clear the annotation canvas
    annotationContext.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);
    loadAnnCat(defaultMode);
}

// --------------------------------------------------------------------------------------------
// EXPORT

// Event listener for the "Export Annotations" button
document.getElementById('export-button').addEventListener('click', function () {
    debouncedExportAnn();
});

// implement debouncing for exportAnn
let exportAnnTimer = null;

function debouncedExportAnn() {
    clearTimeout(exportAnnTimer);
    exportAnnTimer = setTimeout(exportAnn, 500);
};

function exportAnn(){
    if (isMergingMode) {
        alert("Invalid Action. You must merge prefilled annotations first.");
    }
    else {
        console.log("exporting image")
        const image_id = getImageID();
        exportAnnotation(image_id);
    }
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
            data = JSON.parse(data);
            console.log('Sent image id to server for export request'); 
            filename = id+"_annotations.json";
            promptDownload(data, filename);
        },
        error: function (xhr) { 
            console.log('Error sending image id to server for export request');
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

function setup() {
    console.log("loading image");
    loadImage();
    loadAnnCat(defaultMode);
}

// Update the image canvas
$('document').ready(setup);

// --------------------------------------------------------------------------------------------
// REMOVE ANNOTATIONS

document.getElementById('remove-polygon-button').addEventListener('click', function(){
    debouncedRemovePolygon();
});

// implement debouncing for removePolygon
let removePolygonTimer = null;

function debouncedRemovePolygon() {
    clearTimeout(removePolygonTimer);
    removePolygonTimer = setTimeout(removePolygon, 500);
};

function removePolygon(){
    removePolygonMode = !removePolygonMode; // Toggle removePolygonMode
    
    // Change the cursor style and button color on the annotation canvas
    if (removePolygonMode) {
        deleteAnnMode();

        annotationCanvas.style.cursor = 'crosshair';
        document.querySelector('#remove-polygon-button').value = 'Stop removing annotation';
        // Show alert message
        alert("Removing annotations cannot be undone. To stop removing annotations, click on this button again. To disable deletion confirmation, toggle the 'Confirm Deletion' switch below this button.");
        
    } else {
        defaultMode();

        annotationCanvas.style.cursor = 'default';
        document.querySelector('#remove-polygon-button').value = 'Remove annotation';
    }
}

annotationCanvas.addEventListener('click', function(event) {
    debouncedCanvasClick(event);
});

// implement debouncing for canvasClick
let canvasClickTimer = null;

function debouncedCanvasClick(event) {
    clearTimeout(canvasClickTimer);
    canvasClickTimer = setTimeout(function () {canvasClick(event)}, 500);
};

function canvasClick(event){
    // console.log("removePolygonMode " + removePolygonMode)
    if (removePolygonMode) {
        // Get click coordinates
        const rect = annotationCanvas.getBoundingClientRect();
        const scaleX = annotationCanvas.width / rect.width;    // Scaling factor for X
        const scaleY = annotationCanvas.height / rect.height;  // Scaling factor for Y
        const scaledX = (event.clientX - rect.left) * scaleX;
        const scaledY = (event.clientY - rect.top) * scaleY;
        // console.log("clicked points", {scaledX, scaledY});

        // Detect which polygon was clicked
        let polygonIndex = detectPolygon(scaledX, scaledY, all_polygons);
        // console.log("polygonIndex " + polygonIndex);
        if (polygonIndex !== -1) {
            // console.log("here", all_polygons[polygonIndex].annotationId);
            let selected_annotationId = all_polygons[polygonIndex].annotationId; // Assuming each polygon has an 'annotationId' property
            console.log("selected_annotationId", selected_annotationId);
            // Remove the polygon and redraw

            all_polygons.splice(polygonIndex, 1); // Need to de-comment back

            var confirmed = false;
            if (confirm_delete) confirmed = confirm("Are you sure you want to delete this annotation with annotation id "+selected_annotationId+"?");
            if (!confirm_delete || confirmed) {
                // Send updated data to the server and redraw the canvas after successful update
                deleteAnnotation(selected_annotationId, function() {
                    redrawAnnotationCanvas(deleteAnnMode); // Redraw the canvas here
                });
            }
        }
        // document.getElementById('remove-polygon-button').style.backgroundColor = '#000000';
    }
}
function detectPolygon(x, y, all_polygons) {
    for (let i = all_polygons.length-1; i >= 0; i--) {
        const polygonPoints = all_polygons[i].points;
        // console.log("polygonPoints", polygonPoints);

        if (isPointInsidePolygon(x, y, polygonPoints)) {
            return i;  // Return the index of the all_polygons element that contains the polygon
        }
    }
    console.log("Failed to remove annotation.");
    // alert("Failed to remove annotation."); // Alert the user
    return -1; // Return -1 if the point is not inside any polygon
}

function isPointInsidePolygon(x, y, points) {
    console.log("Points Array:", points); // This will show the structure of the points array

    let inside = false;
    // console.log("length: ", points.length);
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
        const xi = points[i].x, yi = points[i].y;
        // console.log("xi", xi);
        const xj = points[j].x, yj = points[j].y;
        // console.log("xj", xj);
        const intersect = ((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        // console.log("intersect", intersect);
        if (intersect) inside = !inside;
    }
    return inside;
}

function deleteAnnotation(annotationId, callback) {
    const data = { annotation_id: annotationId };

    fetch('/update_polygons', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        clearEmphasis();
        callback();
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("Please contact system admin..Failed to remove annotation. " +annotationId ); // Alert the user
    });
}

//--------------------------------------------------------------------------------------------
// PREFILL

let isMergingMode = false
let isPrefillMode = false
let k =  0
let suppix_num = 0
let suppixel_coords = []
let kmeans_labels = []
let segments = []

function showSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('cover-spin').style.display = 'block';
}

function hideSpinner() {
    // document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('cover-spin').style.display = 'none';
}


function drawPrefill(data, draw=true) {
    segments = data["segments"];

    if (draw) {
        console.log('drawing prefill')
        suppixel_coords = data["suppixel_coords"];
        kmeans_labels = data["kmeans_labels"];
        saved = []
        
        let colors = data["colors"];
        let num_superpixels = suppixel_coords.length;
        
        // set transparency
        annotationContext.globalAlpha = 0.4

        // draw and color each polygon 
        for (let suppix_num = 0; suppix_num < num_superpixels; suppix_num++) {
            if (isMergingMode){
                all_polygons.push(suppixel_coords[suppix_num])
            }
            let kmean_label = kmeans_labels[suppix_num]
            let r = colors[kmean_label][0];
            let g = colors[kmean_label][1];
            let b = colors[kmean_label][2];
            let size = suppixel_coords[suppix_num].length; // num of points in a super pixel
            let color = "rgb("+r+", "+g+", "+b+")"; 
            // console.log("color", color)

            let coords_loaded_lines = 0;

            // connect the points
            annotationContext.strokeStyle = color; // Set the polygon line color
            annotationContext.fillStyle = color; // Set the polygon line color
            annotationContext.lineWidth = 2; // Set the polygon line width
            annotationContext.beginPath();

            pts = []
            // connect points in this polygon 
            for (let point_num = 0; point_num < size; point_num = point_num+5) {
            // for local: for (let point_num = 0; point_num < size; point_num = point_num+2) {
                // save some of original points for future saving after merging
                let x = suppixel_coords[suppix_num][point_num][0];
                let y = suppixel_coords[suppix_num][point_num][1];

                if (point_num % 10 == 0){
                // for local:    if (point_num % 1 == 0){
                  pts.push([x,y]);  
                }
                
                // scale polygons to original image dimensions
                x = (x*scaleFactor)+xOffSet;
                y = (y*scaleFactor)+yOffSet;

                annotationContext.arc(x, y, 3, 0, Math.PI * 2, true);
                coords_loaded_lines = coords_loaded_lines + 1;

                if (point_num == 0) { 
                    annotationContext.moveTo(x, y);
                } else {
                    annotationContext.lineTo(x, y);
                }        
            }
            saved.push(pts)
            annotationContext.fill();
            annotationContext.closePath();
            annotationContext.stroke();
            console.log("One new polygon should be drawn");
        }
    }
    autoAnnotationMode();
    console.log("Prefill function finished");
    return saved;
}


let prefill_request = null; 
function getPrefill(k, suppix_num) {
    console.log('prefilling request')
    // Show the spinner
    showSpinner();

    // Using AJAX:
    if (prefill_request != null)
        prefill_request.abort();
    let prefillData = {
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'application/json' 
        },
        type: 'POST',
        url: '/prefill', // function in annotate.py 
        data: JSON.stringify({'image_path' : image_path, 'k':k, 'suppix_num' : suppix_num}),
        cache: false, // not sure what this does but Indu says we might need it
        success: function (data) { // upon success, this function will be executed
            console.log('Sent k value and super pixel number to server for prefill request'); 
            if (data['success']) {
                drawPrefill(data);
                isMergingMode = true;
            } else {
                alert("No annotations generated.");
            }
            hideSpinner(); // Hide spinner on success
            alert("You may click on annotations that you would like to remove. The annotations will only dispapear after you click 'Complete auto-annotation', which will remove the desired annotations as well as merge adjacent annotations of the same category.")
            annotationCanvas.style.cursor = 'crosshair';
        },
        error: function () { 
            console.log('Error sending k value and super pixel number to server for prefill request');
            hideSpinner(); // Hide spinner on error
        }
    };
    prefill_request = $.ajax(prefillData);
}

// Event listener for the "Annotate" button
document.getElementById('prefill-button').addEventListener('click', function () {
    debouncedPrefill();
});

// implement debouncing for prefill
let prefillTimer = null;

function debouncedPrefill() {
    clearTimeout(prefillTimer);
    prefillTimer = setTimeout(prefill, 500);
};

function prefill(){
        autoAnnotationMode();
    
        isPrefillMode = true;
        console.log('Automatically annotate request')
    
        do {
            k = prompt("Select K value from 2 to 5.");
            console.log(k)
            console.log(isNaN(k))
            numK = parseFloat(k);
        
            // Check if the input is null (user clicked cancel)
            if (k === null) {
                defaultMode();
                return; // You can handle cancellation in your code
            } if (isNaN(k) || !Number.isInteger(numK) || (numK < 2 || numK > 5)) { // Check if the input is not a number or outside the range
                alert("Invalid k value. Please enter an integer between 2 and 5.");
                defaultMode();
            } else { // If all conditions are met, break out of the loop
                break;
            }
        } while (true);
    
        do {
            suppix_num = prompt("Select number of super pixels from 10 to 200.");
            numSuppix = parseFloat(suppix_num)
            console.log(!Number.isInteger(numSuppix))
        
            // Check if the input is null (user clicked cancel)
            if (suppix_num === null) {
                defaultMode();
                return; // You can handle cancellation in your code
            // Check if the input is not a number or outside the range
            } else if (isNaN(suppix_num) || !Number.isInteger(numSuppix) || (numSuppix < 10 || numSuppix > 200)) {
                alert("Invalid number of superpixels. Please enter an integer between 10 and 200.");
                defaultMode();
            // If all conditions are met, break out of the loop
            } else {
                break;
            }
        } while (true);
        getPrefill(numK, numSuppix)
}

// ---------------------------------------------------------------------
// MERGING

let getIndexRequest = null;

// how to make this return the index?
function getIndexOfRemovedPixel(pt, suppixel_coords) {
    // Multiply the annotation coordinates by the inverse of the scale factor
    let p = pt;

    // Using AJAX:
    if (getIndexRequest != null)
    getIndexRequest.abort();
    let indexData = {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        type: 'POST',
        url: '/identify_superpixel',
        data: JSON.stringify({'point' : p, 'suppix_cords' : suppixel_coords}),
        cache: false,
        success: function (index) {
            messagebox("Superpixel detected, will be removed after completion of auto-annotation.");
            console.log(index);
            console.log('Received index of removed super pixel');
        },
        error: function () {
            console.log('Error receiving index of removed super pixel');
        }
    };
    getIndexRequest = $.ajax(indexData);
    return getIndexRequest['index'];
}

let merge_request = null;
let merge_labels = null;
function getMerged(image_path, kmeans_labels, segments) {
    // Show the spinner
    showSpinner();
    let labels = null;
    // Using AJAX:
    if (merge_request != null)
    merge_request.abort();
    let mergeData = {
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'application/json' 
        },
        type: 'POST',
        url: '/merge', // function in annotate.py 
        data: JSON.stringify({'image_path' : image_path, 'klabels':kmeans_labels, 'segments' : segments}),
        cache: false, // not sure what this does but Indu says we might need it
        success: function (data) { // upon success, this function will be executed
            console.log('Sent klabels and segments to server for merge request'); 
            // resetCanvas()
            console.log('Canvas cleared. New annotations incoming.'); 
            suppixel_coords = drawPrefill(data);
            console.log("num annotations: ", suppixel_coords.length)
            console.log("annotations: ", suppixel_coords)
            num_kmeans = suppixel_coords.length;
            clearAnnotations();
            clearEmphasis();
            // showSpinner();

            console.log("data.kmeans_labels: ", data.kmeans_labels)
            for (let i = 0; i < suppixel_coords.length; i++) {
                const polygonPoints = suppixel_coords[i];
                console.log("i-th pixel saved: ", i)

                const categoryName = "Category " + kmeans_labels[i] + " Auto " + getImageID();

                // Synchronous AJAX call to get or create the category
                $.ajax({
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    type: 'POST',
                    url: '/get_or_create_category',
                    data: JSON.stringify({'category_name': categoryName}),
                    cache: false,
                    async: false,  // Make this call synchronous
                    success: function (response) {
                        const categoryId = response.categoryId;
                        saveKmeansAnnotation(polygonPoints, categoryId);
                    },
                    error: function (xhr, textStatus, errorThrown) {
                        console.log('Error in getting category ID:', textStatus, errorThrown);
                        // Extract error message from server response
                        var errorMessage = 'Error in getting category ID';
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMessage = xhr.responseJSON.message;
                        }
                        // alert(errorMessage);
                        messagebox(errorMessage);
                        hideSpinner(); // Hide spinner on error
                        defaultMode();
                        loadAnnCat(defaultMode);
                    }
                });
            }
        },
        error: function () { 
            console.log('Error sending klabels and segments to server for merge request');
            hideSpinner(); // Hide spinner on error
            defaultMode();
        }
    };
    merge_request = $.ajax(mergeData);
}

// disappearing message
let setting_timeout = false
function messagebox(msg, duration="5000") {
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

// Event listener for the "Finish Merging" button
document.getElementById('merge-button').addEventListener('click', function () {
    debouncedMerge();
});

// implement debouncing for merging
let mergeTimer = null;

function debouncedMerge() {
    clearTimeout(mergeTimer);
    mergeTimer = setTimeout(merge, 500);
};

function merge(){
    isPrefillMode = false;
    console.log('Merge button request')

    if (!isMergingMode) {
        alert("Invalid Action. You can only merge prefilled annotations.")
    }
    else {
        annotationCanvas.style.cursor = 'auto';
        console.log('Merging in progress.');
        getMerged(image_path, kmeans_labels, segments);
    }
    isMergingMode = false;
}

function saveKmeansAnnotation(coords, categoryId) {
    const transformedCoords = coords.map(
        point => ({
        x: (point[0] * scaleFactor) + xOffSet,
        y: (point[1] * scaleFactor) + yOffSet
        }));

    const image_id = getImageID();
    // console.log("saving annotation with img id " + image_id);
    
    // Send the annotation data to the server
    const annotationData = JSON.stringify({ 
        new_image_id: image_id, // Loaded from page URL
        category_id: categoryId, // generated cat id for this group
        seg_coords: transformedCoords, // Transformed coordinates
        bound_coords: [(5,6),(7,8)], // Example bounds
        new_area: 4, 
        new_iscrowd: true,
        new_isbbox: true, 
        new_color: true
    });

    sendKmeansAnnotationToServer(annotationData, function(annotation_id) {
        // This code will execute after the AJAX request completes
        polygons.push({ points: transformedCoords, annotationId: annotation_id });
        polygons.forEach(polygon => {
            const { points, annotationId } = polygon; // Destructuring to get properties
        });
        num_kmeans_saved += 1;
        console.log("num_kmeans_saved: "+num_kmeans_saved+"/"+num_kmeans);
        if (num_kmeans_saved == num_kmeans) {
            console.log("done with all kmeans, redrawing canvas");
            redrawCanvas();
            num_kmeans_saved = 0;
            num_kmeans = null;
        }
    });
}

// Function to send annotation data to the server
function sendKmeansAnnotationToServer(annotationData, callback) {
    const scaledAnnotationData = JSON.parse(annotationData);
    console.log("annotationData ", annotationData)
    console.log("scaledAnnotationData ", scaledAnnotationData)
    scaledAnnotationData.seg_coords = scaledAnnotationData.seg_coords.map(
        point => ({ x: point.x * scaleFactor, y: point.y * scaleFactor })
    );

    console.log("Sending Annotation Data to Server:", scaledAnnotationData);

    $.ajax({
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        type: 'POST',
        url: '/save_kmeans_annotations',
        data: JSON.stringify(scaledAnnotationData),
        cache: false,
        success: function (response) {
            console.log('Response from Server:', response);
            if (response.hasOwnProperty('annotationId') && response.annotationId >= 0) {
                callback(response.annotationId);
            } else {
                // Display error message to the user
                alert('Error: ' + (response.message || 'Failed to save annotation. No annotation ID returned from server.'));
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log('Error saving annotation data:', textStatus, errorThrown);
            // Extract error message
            var errorMessage = jqXHR.responseJSON && jqXHR.responseJSON.error ? jqXHR.responseJSON.error : textStatus;
            // alert('Error saving annotation data: ' + errorMessage);
            messagebox('Error saving annotation data: ' + errorMessage);
            hideSpinner(); // Hide spinner on error
            defaultMode();
            loadAnnCat(defaultMode);
        }
    });
}

// --------------------------------------------------------------------------------------------
// TOGGLE VIEW

document.getElementById('viewToggle').addEventListener('change', function() {
    debouncedViewToggle();
});

// implement debouncing for deleteAll
let viewToggleTimer = null;

function debouncedViewToggle() {
    clearTimeout(viewToggleTimer);
    viewToggleTimer = setTimeout(viewToggleFunction, 500);
};

function viewToggleFunction() {
    if (!document.getElementById('viewToggle').checked) {
        stored_annotation_canvas = annotationCanvas;
        annotation_parent.removeChild(annotationCanvas);

        stored_emphasis_canvas = emphasisCanvas;
        emphasis_parent.removeChild(emphasisCanvas);
    } else {
        annotation_parent.appendChild(stored_annotation_canvas);
        annotationCanvas = stored_annotation_canvas;
        annotation_parent = annotationCanvas.parentNode;
        annotationContext = annotationCanvas.getContext('2d');

        emphasis_parent.appendChild(stored_emphasis_canvas);
        emphasisCanvas = stored_emphasis_canvas;
        emphasis_parent = emphasisCanvas.parentNode;
        emphasisContext = emphasisCanvas.getContext('2d');
    }
}

function flashEmphasis () {
    stored_emphasis_canvas = emphasisCanvas;
    setTimeout(function () {   
        emphasis_parent.removeChild(emphasisCanvas);
        setTimeout(function () {   
            emphasis_parent.appendChild(stored_emphasis_canvas);
            emphasisCanvas = stored_emphasis_canvas;
            emphasis_parent = emphasisCanvas.parentNode;
            emphasisContext = emphasisCanvas.getContext('2d');
            setTimeout(function () {   
                emphasis_parent.removeChild(emphasisCanvas);
                setTimeout(function () {   
                    emphasis_parent.appendChild(stored_emphasis_canvas);
                    emphasisCanvas = stored_emphasis_canvas;
                    emphasis_parent = emphasisCanvas.parentNode;
                    emphasisContext = emphasisCanvas.getContext('2d');
                }, 150);
            }, 150);
        }, 150);
    }, 150);
}

function clearAnnotations() {
    annotationContext.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);
}