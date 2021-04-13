import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/styles';
import { Button, ButtonGroup, Card, CardContent, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Grid, TextField, Typography, Box } from '@material-ui/core';
import { api, Auth, baseurl } from 'api';
import { DataGrid } from '@material-ui/data-grid';
import ModelSearchComponent from 'components/ModelSearchComponent/ModelSearchComponent';
import FileSaver from 'file-saver';
import Chip from "@material-ui/core/Chip";
import Autocomplete from "@material-ui/lab/Autocomplete";

const useStyles = makeStyles(theme => ({
    root: {
        padding: theme.spacing(4),
        // overflowX: 'hidden',
    },
    reviewTable: {
        backgroundColor: 'white'
    },
    searchField: {
        width: '70%',
    },
    headerRow: {
        height: '12vh'
    }
}));


/* ------------------------------------
*  Loads the details on available images into client.
*  This will take into account the filters applied from
*  the basic/advanced search feature.
**/
async function loadImageDataFromServer(dataFilter, searchString) {
    let httpRequestDetails = {
        url: baseurl + api['search_images'],
        method: 'post',
        params: { 'page_id': -1 },
        headers: { 'Authorization': 'Bearer ' + Auth.token, 'content-type': 'application/json' }
    };

    if (Object.keys(dataFilter).length !== 0) {
        httpRequestDetails['data'] = { 'search_filter': dataFilter };
    }

    if (searchString.length > 0) {
        httpRequestDetails['params']['search_string'] = searchString;
    }

    let response = await axios.request(httpRequestDetails)

    return response;
}


async function loadRowsFromServer(pageNumber, dataFilter, searchString) {

    // Generate page params and the body
    let httpRequestDetails = {
        url: baseurl + api['search_images'],
        method: 'post',
        params: { 'page_id': pageNumber.toString() },
        headers: { 'Authorization': 'Bearer ' + Auth.token, 'content-type': 'application/json' }
    };

    if (Object.keys(dataFilter).length !== 0) {
        httpRequestDetails['data'] = { 'search_filter': dataFilter };
    }

    if (searchString.length > 0) {
        httpRequestDetails['params']['search_string'] = searchString;
    }

    // First we request the list of image hashes on this page, then we load the data for those hashes
    let response = await axios.request(httpRequestDetails);

    if (response.data['status'] === 'failure') {
        console.log('[Error] Unable to load row data.')
        return []; // Return empty rows if unable to load 
    }

    let imageHashes = response.data['hashes'];

    httpRequestDetails = {
        url: baseurl + api['image_result'],
        method: 'post',
        data: imageHashes,
        headers: { 'Authorization': 'Bearer ' + Auth.token, 'content-type': 'application/json' }
    }
    response = await axios.request(httpRequestDetails);

    let newImageData = [];

    response.data.forEach((imageModelResult) => {
        if (imageModelResult['status'] === 'success') {
            let rowData = {
                id: imageModelResult['hash_md5'],
                hash_md5: imageModelResult['hash_md5'],
                file_names: imageModelResult['file_names'].join(', '),
                users: imageModelResult['users'],
                tags: (imageModelResult['tags'])?imageModelResult['tags']:[],
            };
            newImageData.push(rowData);
        }
    });

    return newImageData;
}

/* ------------------------------------
*  Update tags for an image with an input hash
*  Return true, if success.  Otherwise, return false.
**/
async function updateImageTags(image_hash, tags) {
    // set body message
    const md5_hashes = [image_hash]
    const post_data = {
        "md5_hashes": md5_hashes,
        "new_tags": tags
    }

    // setup config
    const config = {
        'Authorization': 'Bearer ' + Auth.token,
        'content-type': 'application/json',
    };

    // create http request details
    let httpRequestDetails = {
        url: baseurl + api['update_tag'],
        method: 'post',
        data: post_data,
        params: {"username": Auth.user["username"] },
        headers: config
    };

    // send request to update the tags
    try {
        let response = await axios.request(httpRequestDetails);
        if (response.data[0]['status'] === 'success') {
            return true;
        }
    } catch(err) {
        // error can be 404 or etc
        console.log(err)
        return false;
    }
    console.log('[Error] Failed to update tags.')
    return false; // fail to update tags

}

const Review = () => {
    const classes = useStyles();
    const maxTagShown = 4; // maximum number of tags thhat can be shown

    // General Image Data from Server
    const [pagesTotal, setPagesTotal] = useState(0); // Number of pages in table
    const [pageSize, setPageSize] = useState(0); // Number of images on 1 page of table
    const [numImagesTotal, setNumImagesTotal] = useState(0); // Total images we can see
    const [modelList, setModelList] = useState({});  // Stores all models we can search by

    // Image Result Table
    const [loading, setLoading] = useState(false); // Loading bar showing in table
    const [rows, setRows] = useState([]); // Current data being shown in table


    // Searching
    const [searchTextfieldValue, setSearchTextfieldValue] = useState(''); // String search query before being saved
    const [generalSearchQuery, setGeneralSearchQuery] = useState(''); // String search query
    const [modelSearchQuery, setModelSearchQuery] = useState(''); // String search query
    const [advancedSearchOpen, setAdvancedSearchOpen] = useState(false); // Advanced search dialog open
    const [advancedSearchFilter, setAdvancedSearchFilter] = useState({}); // Advanced search filter
    const [usingSearchFilter, setUsingSearchFilter] = useState(false);
    const [tagsDialogOpen, setTagDialogOpen] = useState(false); // Tag dialog open
    const [tagsInDialog, setTagsInDialog] = useState([]); // Current data being shown in table
    const [dataInDialog, setDataInDialog] = useState({}); // Current data being shown in table
    const [tempTagsInDialog, setTempTagsInDialog] = useState([]); // Current data being shown in table

    // On RowSelected, open a popup for adding tags
    function handleRowSelected(param: GridRowSelectedParams) {
        // param.data
        const tags = param.data.tags.toString();
        if(tags !== "") {
            setTagsInDialog(tags.split(','));
        } else {
            setTagsInDialog([]);
        }
        setTempTagsInDialog(tagsInDialog)
        setTagDialogOpen(true);
        setDataInDialog(param.data)
    }

    // Save tags from Dialog
    async function saveTags() {

        // Call update tags API
        const isSuccess = await updateImageTags(dataInDialog.hash_md5, tempTagsInDialog);
        if(isSuccess) {
            // successfully updated to the backend, thhen update the UI.
            const result = rows.find((e) => e.hash_md5 === dataInDialog.hash_md5)
            result.tags = tempTagsInDialog
        } else {
            console.log("Update tags failed.")
        }

        setTagDialogOpen(false)

    }

    // save tags to temporary list
    function handleTagsChanged(values) {
        // Stored temp tags for upload to server later
        setTempTagsInDialog(values)
    }

    const tagsAutoComplete = [
        {value: "Coke"},
        {value: "Cat"}
    ] // Strings for tags autocomplete, this should not be a static list, it should load from Database in the future


    // Export the data shown on the table to a CSV file
    function downloadDataAsCSV() {
        let csvData = 'Image MD5 Hash, Filenames, Tags\n'

        for(let i=0; i < rows.length; i++){

            // const t = (rows[i].tags[0])?rows[i].tags[0]:""
            const t = "";
            csvData += rows[i].hash_md5 + ',"' + rows[i].file_names + '","' + t + '"\n';
        }

        var blob = new Blob([csvData], { type: "text/csv;charset=utf-8" });
        FileSaver.saveAs(blob, "Search Results.csv");
    }

    // Table columns
   const columns: ColDef[]  = [
        { field: 'file_names', headerName: 'File Names', width: 300 },
        { field: 'users', headerName: 'Users', width: 200 },
        { 
            field: 'tags', 
            headerName: 'Tags', 
            width: 300, 
            sortable: false,
            renderCell: (params: CellParams) => (
                <div>
                {
                    // need to fix this after the backend is connected, now it somehow stores array in string
                    (params.value)?params.value.toString().split(',').splice(0,maxTagShown).map((tag, index) => (
                        tag !== ""
                        ? index < maxTagShown-1
                        ? (<Chip
                          color="secondary"
                          variant="default"
                          label={tag}
                          key={index}
                        />)
                        : (<Chip
                          color="secondary"
                          variant="default"
                          label={"+" + (params.value.toString().split(',').length - index).toString()}
                          key={index}
                        />)
                        : <div key={index}></div>
                  )):""
                }
                </div>
            )


        },
        { field: 'hash_md5', headerName: 'MD5 Hash', width: 250, sortable: false },
    ];

    // This will run initially on page load
    useEffect(() => {

        // Load in the image data (num images, per page, etc)
        const imageLoadHelper = async () => {
            let response = await loadImageDataFromServer({}, '');
            setPagesTotal(response.data['num_pages']);
            setPageSize(response.data['page_size']);
            setNumImagesTotal(response.data['num_images']);
        }
        imageLoadHelper();



        // Get all available models that we can filter by
        axios.request({
            url: baseurl + api['model_result_list'],
            method: 'get',
            headers: { 'Authorization': 'Bearer ' + Auth.token }
        }).then((response) => {
            setModelList(response.data['models']);
        }).catch((error) => {
            if (error.response) {
                console.log("[Error] Initial model list load failure", error);
            } else {
                console.log("[Error] Initial model list load failure");
            }
        })

    }, []);

    // When we change the filter being used, we should reload the images that
    // are available with the filter applied
    async function runSearch() {

        let response = await loadImageDataFromServer(advancedSearchFilter, searchTextfieldValue);

        setGeneralSearchQuery(searchTextfieldValue);
        setUsingSearchFilter(true);
        setAdvancedSearchOpen(false);
        setPagesTotal(response.data['num_pages']);
        setPageSize(response.data['page_size']);
        setNumImagesTotal(response.data['num_images']);
    }

    async function clearSearch() {
        let response = await loadImageDataFromServer({}, '');

        setPagesTotal(response.data['num_pages']);
        setPageSize(response.data['page_size']);
        setNumImagesTotal(response.data['num_images']);
        setUsingSearchFilter(false);
        setGeneralSearchQuery('');
        setAdvancedSearchFilter([]);
    }

    /* ------------------------------------
     *  Loads a page into the table.
     *  This will take into account the filters applied from
     *  the basic/advanced search feature.
    **/
    const loadRowsFromServerHelper = useCallback((pageNumber) => {

        async function loadRows() {
            let rows;
            if (usingSearchFilter) {
                rows = await loadRowsFromServer(pageNumber, advancedSearchFilter, generalSearchQuery);
            } else {
                rows = await loadRowsFromServer(pageNumber, {}, '');
            }
            setRows([...rows]);
            setLoading(false);
        }
        setLoading(true);
        loadRows();
    }, [usingSearchFilter, generalSearchQuery, advancedSearchFilter]);

    useEffect(() => {
        if (numImagesTotal > 0) {
            loadRowsFromServerHelper(1);
        }
    }, [numImagesTotal, loadRowsFromServerHelper])


    // Helper callback to set search parameters
    function updateSearchFilterFromModelCard(modelName, modelClasses) {
        if (modelClasses.length === 0) {
            let newClasses = { ...advancedSearchFilter };
            delete newClasses[modelName];
            setAdvancedSearchFilter(newClasses);
        } else {
            setAdvancedSearchFilter({ ...advancedSearchFilter, [modelName]: modelClasses });
        }
    }



    return (
        <div className={classes.root}>
            <Grid
                container
                spacing={6}
                direction="column"
            >

                <Grid
                    container
                    justify="center"
                    direction="row"
                    spacing={2}
                >

                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent className={classes.headerRow}>
                                <Typography gutterBottom>
                                    {usingSearchFilter ?
                                        <Typography variant='body1' component='span'>Images Matching Query</Typography>
                                    :
                                        <Typography variant='body1' component='span'>Images Total</Typography>  
                                    }            
                                </Typography>
                                <Typography variant="h5">
                                    {numImagesTotal}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Card className={classes.headerRow}>

                            {usingSearchFilter ?
                                <div>
                                    <CardContent>
                                        <Typography gutterBottom>
                                            Search Filter Applied
                                        </Typography>

                                        <Grid container>
                                            <Grid item xs={6}>
                                                <Button color="primary" variant="contained" fullWidth onClick={clearSearch}>
                                                    Clear Filter
                                                </Button>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Button color="secondary" variant="contained" fullWidth onClick={() => downloadDataAsCSV()}>
                                                    Download Data
                                                </Button>
                                            </Grid>

                                        </Grid>
                                    </CardContent>
                                </div>
                                :
                                <CardContent>
                                    <Typography gutterBottom>
                                        Viewing All Images
                                </Typography>
                                </CardContent>
                            }

                        </Card>
                    </Grid>

                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Grid justify="space-between" container spacing={3} alignItems="center">
                                    <Grid item xs={12} md={8}>
                                        <TextField
                                            variant="outlined"
                                            fullWidth={true}
                                            label='Search Image and Model Data'
                                            defaultValue={generalSearchQuery}
                                            onChange={(e) => { setSearchTextfieldValue(e.target.value); }}
                                            onKeyPress={(e) => { (e.key === 'Enter')?runSearch():void 0; }}
                                        />
                                    </Grid>
                                    <Grid item xs={12} md={4}>

                                        <ButtonGroup size='large'>
                                            <Button
                                                color='primary'
                                                variant='contained'
                                                onClick={() => { setAdvancedSearchOpen(true); }}
                                            >
                                                Advanced
                                            </Button>
                                            <Button color='secondary' variant='contained' onClick={runSearch}>Search</Button>

                                        </ButtonGroup>

                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {pagesTotal > 0 ?
                        <Grid
                            item
                            xs={12}
                        >
                            <Card>
                                <CardContent style={{ height: '60vh' }}>
                                    <DataGrid
                                        onPageChange={(p) => loadRowsFromServerHelper(p.page)}
                                        pageSize={pageSize}
                                        rowCount={numImagesTotal}
                                        rows={rows}
                                        columns={columns}
                                        loading={loading}
                                        pagination
                                        paginationMode="server"                                        
                                        onRowSelected={handleRowSelected}
                                    />
                                </CardContent>
                            </Card>

                        </Grid>
                        :
                        <Grid item sm={12}>
                            <Card>
                                <CardContent style={{ height: '60vh' }}>
                                    <Grid
                                        container
                                        spacing={0}
                                        direction="column"
                                        alignItems="center"
                                        justify="center"
                                    >
                                        <Grid item xs={6} style={{ marginTop: '5vh' }}>
                                            <Typography variant="h2" color={'error'} >
                                                No Images Available.
                                            </Typography>
                                        </Grid>

                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>
                    }
                </Grid>
            </Grid>

            <Dialog
                open={advancedSearchOpen}
                onClose={() => setAdvancedSearchOpen(false)}
                aria-labelledby="form-dialog-title"
                fullWidth={true}
                maxWidth={'lg'}
            >
                <DialogTitle id="form-dialog-title">Advanced Search</DialogTitle>
                <DialogContent
                    style={{ height: '80vh', overflow: 'auto' }}
                >

                    <Grid
                        container
                        spacing={3}
                        display="flex"
                        justify="center"
                    >

                        <Grid item xs={12}><Divider /></Grid>

                        <Grid item xs={4}>
                            <TextField label="Search Models" fullWidth defaultValue={modelSearchQuery} onChange={(e) => setModelSearchQuery(e.target.value)}></TextField>
                        </Grid>


                        <Grid item xs={12}><Divider /></Grid>

                        {Object.keys(modelList).map((modelName) => (
                            modelName.toLowerCase().includes(modelSearchQuery.toLowerCase()) &&
                            <Grid item xs={4} key={modelName}>
                                <ModelSearchComponent
                                    modelName={modelName}
                                    modelClasses={modelList[modelName]}
                                    initialState={advancedSearchFilter[modelName] !== undefined ? advancedSearchFilter[modelName] : []}
                                    onClassSelect={(classList) => updateSearchFilterFromModelCard(modelName, classList)}
                                />
                            </Grid>
                        ))}



                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button color="primary" variant={'contained'} onClick={() => setAdvancedSearchOpen(false)}>
                        Cancel
                    </Button>
                    <Button color="secondary" variant={'contained'} onClick={runSearch}>
                        Search
                    </Button>
                </DialogActions>
            </Dialog>


            <Dialog
                open={tagsDialogOpen}
                onClose={() => setTagDialogOpen(false)}
                aria-labelledby="form-dialog-title"
                fullWidth
                maxWidth="sm"
            >
                <DialogTitle id="form-dialog-title">Edit Tags</DialogTitle>
                <DialogContent
                    style={{ height: '30vh', overflow: 'auto' }}
                >

                    <Grid
                        container
                        spacing={3}
                        display="flex"
                        justify="center"
                    >

                        <Grid item xs={12}><Divider /></Grid>

                        <Grid item xs={10}>
                            <Typography component={'span'} display="inline" >
                            <Box display="flex" flexDirection="row" bgcolor="background.paper">
                                <Box p={1}  fontWeight="fontWeightBold">
                                  Hash:
                                </Box>
                                <Box p={1}  fontWeight="fontWeightRegular">
                                  {dataInDialog.hash_md5}
                                </Box>
                              </Box>
                              <Box display="flex" flexDirection="row" bgcolor="background.paper">
                                <Box p={1}  fontWeight="fontWeightBold">
                                  File Names:
                                </Box>
                                <Box p={1}  fontWeight="fontWeightRegular">
                                  {dataInDialog.file_names}
                                </Box>
                              </Box>

                            </Typography>
                        </Grid>

                        <Grid item xs={12}><Divider /></Grid>

                        <Grid item xs={10}>
                            <Autocomplete
                                multiple
                                id="tags-filled"
                                options={tagsAutoComplete.map((option) => option.value)}
                                defaultValue={tagsInDialog}
                                freeSolo
                                renderTags={(value, getTagProps) =>
                                  value.map((option, index) => (
                                    <Chip
                                      color="secondary"
                                      variant="default"
                                      label={option}
                                      {...getTagProps({ index })}
                                    />
                                  ))
                                }
                                onChange={ (event, values) => handleTagsChanged(values) }                                          
                                renderInput={(params) => (
                                  <TextField
                                    {...params}
                                    variant="outlined"
                                    label="Tags"
                                    placeholder="Add more tags here"
                                  />
                                )}
                              />
                        </Grid>



                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button color="primary" variant={'contained'} onClick={() => setTagDialogOpen(false)}>
                        Cancel
                    </Button>
                    <Button color="secondary" variant={'contained'} onClick={saveTags}>
                        Save
                    </Button>
                </DialogActions>
            </Dialog>

        </div>
    );
};

export default Review;
