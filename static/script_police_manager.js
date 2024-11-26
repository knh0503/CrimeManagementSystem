//script_police_manager.js

document.getElementById("change_region_button").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("change_region").style.display = "block";
});

document.getElementById("enroll_crime_button").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("enroll_crime").style.display = "block";
    print_report_list();
});

document.getElementById("view_change_offender_button").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("view_change_offender").style.display = "block";
});

document.getElementById("enroll_investigation_button").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("enroll_investigation").style.display = "block";
    print_non_investigation_list();
});

document.getElementById("crime_risk_prediction_button").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("crime_risk_prediction").style.display = "block";
});

function re_enter() {
    document.getElementById("crime_risk_prediction_form").style.display = "block";
    document.getElementById("prediction_result").style.display = "none";
}

function load_police() {
    document.getElementById('change_region_table').style.display = 'block';
    var region = document.getElementById("old_region").value;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_police?region=" + region, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            document.getElementById("tableBody").innerHTML = xhr.responseText;
        }
    };
    xhr.send();
}


function select_new_region(button) {
    var region = document.getElementById("old_region").value;
    var tdElement = button.parentNode;
    var trElement = tdElement.parentNode;
    var id = trElement.querySelector('#police_id').innerText;
    var new_region = trElement.querySelector('#new_region').value;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/select_police?new_region=" + new_region + "&id=" + id + "&region=" + region, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            alert_msg = xhr.responseText;
            alert(alert_msg);
            load_police();
        }
    };
    xhr.send();
}


function print_report_list() {
    axios.post('/get_report_list')
        .then(function(response) {
            document.getElementById("tableBody_report").innerHTML = response.data;
        })
        .catch(function(error){
            console.error('에러 발생: ', error);
        });
}

function toggleTextbox(checkbox) {
    //offender_info div 확인
    const div_elem = document.getElementById("offender_info");
    // 체크박스 선택 여부 체크 -> 선택 여부에 따라 div 활성화/비활성화
    div_elem.style.display = checkbox.checked ? "block" : "none";
}

$(document).ready(function() {
    $("#region_offender_form").submit(function(e) {
        document.getElementById("offender_table").style.display = "block";
        e.preventDefault();
        // var region_offender = document.getElementById("region_offender").value;
        // $("#result").text("처리된 데이터: " + region_offender)
        $.ajax({
            type: "POST",
            url: "/view_region_offender",
            data: $(this).serialize(),
            success: function(data) {
                $("#offender_table_body").html(data.offender_html);
                $("#result_message").html(data.message);
                if (data.police_html !== "") {
                    document.getElementById("police_table").style.display = "block";
                    $("#police_table_body").html(data.police_html); 
                  }               
            }
        });
    });
});

function print_non_investigation_list() {
    $.ajax({
        url: "/get_non_investigation_list",
        type: "POST",
        success: function(response) {
            $("#non_investigation_crime_table_body").html(response);
        },
        error: function(xhr, status, error) {
            console.error("AJAX 요청 실패:", status, error);
        }
    });
}

$(document).ready(function() {
    $("#investigation_form").submit(function(e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: "/investigation",
            data: $(this).serialize(),
            success: function(response) {
                document.getElementById("investigation_table").style.display = "block";
                $("#investigation_table_body").html(response);           
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("crime_risk_prediction_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/crime_risk_prediction', formData)
            .then(function(response) {
                document.getElementById("crime_risk_prediction_form").style.display = "none";
                document.getElementById("prediction_result").style.display = "block";
                document.getElementById("prediction_result").innerHTML = response.data;
            })
            .catch(function(error) {
                console.error('Error:', error);
                let errorMessage = "오류가 발생했습니다.";
                if (error.response && error.response.data) {
                    errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                }
                swal.fire({
                    title: "오류",
                    html: errorMessage,
                    icon: "error",
                    confirmButtonText: "확인"
                });
            });
    });
});