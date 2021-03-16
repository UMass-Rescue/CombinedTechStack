import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/styles';
import { Button, ButtonGroup, Card, CardContent, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Grid, TextField, Typography } from '@material-ui/core';
import { api, Auth, baseurl } from 'api';
import { DataGrid } from '@material-ui/data-grid';
import ModelSearchComponent from 'components/ModelSearchComponent/ModelSearchComponent';
import FileSaver from 'file-saver';

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
            };
            newImageData.push(rowData);
        }
    });

    return newImageData;
}


async function downloadImageHashesFromServer(dataFilter, searchString) {
    let httpRequestDetails = {
        url: baseurl + api['search_image_download'],
        method: 'post',
        params: {},
        headers: { 'Authorization': 'Bearer ' + Auth.token, 'content-type': 'application/json' }
    };

    if (Object.keys(dataFilter).length !== 0) {
        httpRequestDetails['data'] = { 'search_filter': dataFilter };
    }

    if (searchString.length > 0) {
        httpRequestDetails['params']['search_string'] = searchString;
    }

    let response = await axios.request(httpRequestDetails);

    if (response.data['status'] === 'success') {
        let hashes = response.data['hashes'];

        let csvData = 'Image MD5 Hash\n'

        hashes.forEach((hash) => {
            csvData += hash + '\n';
        });

        var blob = new Blob([csvData], { type: "text/csv;charset=utf-8" });
        FileSaver.saveAs(blob, "Search Results.csv");

    }
}

const Review = () => {
    const classes = useStyles();

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


    // Table columns
    const columns = [
        { field: 'file_names', headerName: 'File Names', width: 300 },
        { field: 'users', headerName: 'Users', width: 300 },
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
                                                <Button color="secondary" variant="contained" fullWidth onClick={() => downloadImageHashesFromServer(advancedSearchFilter, generalSearchQuery)}>
                                                    Download Hashes
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

        </div>
    );
};

export default Review;
