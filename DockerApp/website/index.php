
<html>
    <head>
        <title>CIS 322 REST-api: Brevet Controle List</title>

        <!-- Javascript:  JQuery from a content distribution network (CDN) -->
        <script
            src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js">
        </script>
    </head>

    <body>
        <h1>GET Controle Information</h1>

        <form action="" method='GET'>
            <label>Control List</label>
                <select name="control_list" id="control_list">
                    <option value='listAll'>List All</option>
                    <option value='listOpenOnly'>List Open Only</option>
                    <option value='listCloseOnly'>List Close Only</option>
                </select>
            <label>Format</label>
                <select name="format" id="format">
                    <option value='json'>JSON</option>
                    <option value='csv'>CSV</option>
                </select>
            <label>Limit</label>
                <input type='number' name='limit' id='limit' min='1' max='20' step='1'>

            <input type="submit" value="Submit">
        </form>

        <h2>Requested Information</h2>

        <?php 
            $list = $_GET['control_list'];
            $format = $_GET['format'];
            $limit = $_GET['limit'];
            $output = file_get_contents("http://api/$list/$format?top=$limit");
            
            if ($format == 'json'){
                echo $output;
            } else{
                foreach (str_getcsv($output, "\n") as $line){
                    echo "<p> $line </p>";
                }
                
            }
        ?>

    </body>
</html>
