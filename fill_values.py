import pandas as pd
import numpy  as np



# Predict closing values by de-collapsing the mean,
# and custom cubic spline interpolation
def pred_from_mean( inp_close_df, roll_nums ):
    
    # Stores values predicted from mean
    my_df = inp_close_df['close'].to_frame()
    
    
    rolls = sorted( roll_nums )
    diff  = np.array( rolls[1:] )-np.array( rolls[:-1] )

    # First predict the first few days, indexing starts at 1
    roll_str = str( rolls[0] )
    mid      = str((rolls[0]+1)/2)
    
    
    my_df['pred_'+roll_str+'_day_1'         ] = my_df['close']
    
    # Odd
#    if ( (rolls[0] % 2) == 1 ):
    my_df['pred_'+str( rolls[0] )+'_day_'+mid ] = inp_close_df['pred_mean_'+roll_str]

    my_df['pred_'+roll_str+'_day_'+roll_str ] =  2 * inp_close_df['pred_mean_'+roll_str ] - my_df['close']

    # Find values not covered
    predicted_list = [1,(rolls[0]+1)/2,rolls[0]]
    need_to_predict = [x for x in range(1,rolls[0]+1) if x not in predicted_list]

    # Find values not covered
    if ( len(need_to_predict) > 0 ):

        # Assemble data needing predicting
        x1 = my_df['pred_'+roll_str+'_day_1'        ]
        x5 = my_df['pred_'+roll_str+'_day_'+roll_str]
        str_pred_list = ['pred_'+roll_str+'_day_1','pred_'+roll_str+'_day_'+roll_str]
        
        if ( (rolls[0] % 2) == 1 ):
            x3 = my_df['pred_'+roll_str+'_day_'+mid]

            str_pred_list = ['pred_'+roll_str+'_day_1',
                             'pred_'+roll_str+'_day_'+mid,
                             'pred_'+roll_str+'_day_'+roll_str]
            
# Interpolation method could potentially be changed        

        # Predict using custom cubic spline, for pandas arrays
        preds = cubic_pandas_spline( predicted_list, my_df[str_pred_list].values, need_to_predict )
        
        # Save the interpolated arrays
        for i in range( 0, len(need_to_predict) ):
            my_df['pred_'+roll_str+'_day_'+str(need_to_predict[i])] = preds[:,i]

        
    # Need to take mean chunks, and calculate amount in later chunk
    # In later chunck, midpoint will be the mean value, interpolate
    #  from previous mean value centerpoint to find chunck x1,
    #  then use ( x5=2m-x1 ) to calcuate chunck x5, interpolate, repeat
        
    for i in range( 1, len(rolls) ):
        
        prev_str   = str(rolls[i-1])
        chunk_str  = str(rolls[i  ])
        
        prev_days  = rolls[i-1]
        tot_days   = rolls[i  ]
        chunk_days = tot_days - prev_days
        
        prev_mean  = inp_close_df['pred_mean_'+ prev_str]
        tot_mean   = inp_close_df['pred_mean_'+chunk_str]

        chunk_mean = ( tot_days*tot_mean - prev_days*prev_mean ) / ( chunk_days )
        
    
        # Odd, use midpoint
        # Will need these values for later iterations anyway
        prev_mid = int(mid)
        mid      = (chunk_days+1)/2
        mid_str  = str(mid)
        
        if ( (chunk_days % 2) == 1 ):


            my_df['pred_'+chunk_str+'_day_'+mid_str ] = chunk_mean
            
            
            # Get the first day from interpolation between two midpoints
            my_df['pred_'+chunk_str+'_day_1' ] = ( (      mid - 1 ) * chunk_mean  +
                                                   ( prev_mid     ) * my_df['pred_'+prev_str+'_day_'+str(prev_mid)] 
                                                 ) / (    mid - 1   + prev_mid ) 

            my_df['pred_'+chunk_str+'_day_'+str(chunk_days) ] =  2 * chunk_mean - my_df['pred_'+chunk_str+'_day_1' ]

            # Find values not covered
            predicted_list = [1,mid,chunk_days]
            need_to_predict = [x for x in range(1,chunk_days) if x not in predicted_list]
            
            # Find values not covered
            if ( len(need_to_predict) > 0 ):

                # Assemble data needing predicting
                x1 = my_df['pred_'+chunk_str+'_day_1'        ]
                x5 = my_df['pred_'+chunk_str+'_day_'+str(chunk_days)]
                str_pred_list = ['pred_'+chunk_str+'_day_1',
                                 'pred_'+chunk_str+'_day_'+mid_str,
                                 'pred_'+chunk_str+'_day_'+str(chunk_days)]

# Interpolation method could potentially be changed        

                # Predict using custom cubic spline, for pandas arrays
                preds = cubic_pandas_spline( predicted_list, my_df[str_pred_list].values, need_to_predict )

                # Save the interpolated arrays
                for i in range( 0, len(need_to_predict) ):
                    my_df['pred_'+chunk_str+'_day_'+str(need_to_predict[i])] = preds[:,i]
                
        # Even
        else:
            # Use mean difference, and difference from chunk to last day
            delta = inp_close_df['pred_mean_'+chunk_str] - my_df['pred_'+prev_str+'_day_'+str(diff[i-1])]
            my_df['pred_'+chunk_str+'_day_1'] = inp_close_df['pred_mean_'+chunk_str] - delta/2.
            my_df['pred_'+chunk_str+'_day_2'] = inp_close_df['pred_mean_'+chunk_str] + delta/2.

            
    return my_df.reindex_axis(sorted(my_df.columns), axis=1)




# Performs interpolations with the data format we have
def cubic_pandas_spline( inp_x, y, pred_x ):
    
    x      = np.array(inp_x)
    pred_x = np.array( pred_x )

    a = np.zeros( [y.shape[0], y.shape[1]+1] )
    b = np.zeros( [y.shape[0], y.shape[1]  ] )
    d = np.zeros( [y.shape[0], y.shape[1]  ] )
    
    h = np.ones( y.shape[1] )+1
    
    for i in range( 0, y.shape[1] ):
        a[:,i] = y[:,i]

    alpha = np.zeros( [y.shape[0], y.shape[1]] )
    alpha[:,1:] = 3./h[1:]*(a[:,2:]-a[:,1:-1]) - 3./h[:-1]*(a[:,1:-1]-a[:,:-2])

    c = np.zeros( [y.shape[0], y.shape[1]  ] )
    l = np.zeros( [y.shape[0], y.shape[1]  ] )
    m = np.zeros( [y.shape[0], y.shape[1]  ] )
    z = np.zeros( [y.shape[0], y.shape[1]  ] )

    l[:,0] = 1
    l[:,y.shape[1]-1] = 1
    
    for i in range( 1, y.shape[1]-1 ):
        l[:,i] = 2 * ( x[i+1] - x[i-1] ) - h[i-1] * m[:,i-1]
        m[:,i] = h[i] / l[:,i]
        z[:,i] = ( alpha[:,i]-h[i-1]*z[:,i-1] ) / l[:,i]
                
    for j in range( y.shape[1]-2, -1, -1 ):
        c[:,j] =  z[:,j]  -  m[:,j] *c[:,j+1]
        b[:,j] =((a[:,j+1]-  a[:,j])/h[  j  ] - 
                 (c[:,j+1]+2*c[:,j])*h[  j  ]/3. )
        d[:,j] = (c[:,j+1]-  c[:,j])/(h[ j  ]*3. )
                
    mid_index = int((y.shape[1])/2)
    
    ret_y = np.zeros( [y.shape[0],pred_x.shape[0]] )

    for i in range( 0, pred_x.shape[0] ):
        ret_y[:,i]= ( 
                 a[:,mid_index]*(pred_x[i]-inp_x[mid_index])**0 +
                 b[:,mid_index]*(pred_x[i]-inp_x[mid_index])**1 +
                 c[:,mid_index]*(pred_x[i]-inp_x[mid_index])**2 +
                 d[:,mid_index]*(pred_x[i]-inp_x[mid_index])**3 )
    
    return ret_y