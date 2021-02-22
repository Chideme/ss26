

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
        

        if (activeTab) {
           $('.nav-tabs a[href="' + activeTab + '"]').tab('show');
        }

        
        
        

        // return to page position after reload ( for driveway updates)
        
        var scrollpos = localStorage.getItem('scrollpos');
        if (scrollpos) window.scrollTo(0,scrollpos);

        window.onbeforeunload = function(e) {
            localStorage.setItem('scrollpos',window.scrollY);
        };
        
        
        // DataTables function
        $('#export').DataTable( {
            dom: '<fli<t>Bp>',
            "lengthMenu": [ 200, 150, 100, 75],
            buttons: [
                'copy',
                'excel',
                'csv',
                'pdf'
            ]
        } );

        
            
// html2pdf
$('#download').on('click',function(){
    var element = document.getElementById('printTable');
    var opt = {
    margin:       [1,1,1,1],
    filename:     document.getElementById('name').innerHTML+'.pdf',
    html2canvas:  { scale: 2, bottom: 0 },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'landscape' ,compressPDF: true},
    pagebreak: { before: "tr"}
    };

  
    // Old monolithic-style usage:
    html2pdf(element, opt);
    })

   
});           
            
            
            

             
