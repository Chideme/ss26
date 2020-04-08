$(document).ready(function(){
        $('a[data-toggle="tab"]').on('shown.bs.tab', function(e){
            localStorage.setItem('activeTab', $(e.target).attr('href'));
        });

        // Here, save the index to which the tab corresponds. You can see it 
        // in the chrome dev tool.
        var activeTab = localStorage.getItem('activeTab');

        // In the console you will be shown the tab where you made the last 
        // click and the save to "activeTab". I leave the console for you to 
        // see. And when you refresh the browser, the last one where you 
        // clicked will be active.
        console.log(activeTab);

        if (activeTab) {
           $('.nav-tabs a[href="' + activeTab + '"]').tab('show');
        }

        //Prints Driveway
        function printTable (){
            var toprint = document.getElementById("printTable");
            newWIn = window.open("");
            newWIn.document.write(toprint.outerHTML);
            newWIn.print();
            newWIn.close();
        };
        $('#print').on('click',function(){
            printTable();
            window.location = 'driveway';
        });

        //Http request to display driveway data to do.
         
        
    });
