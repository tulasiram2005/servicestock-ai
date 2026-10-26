import {expect,test} from 'vitest';
import {driverPoints} from '../app/driver-chart';
test('ranks signed contributions without treating baseline as a driver',()=>{
 expect(driverPoints({lag_1:-3,rolling_mean:2,base_value:10})).toEqual([{feature:'lag_1',contribution:-3},{feature:'rolling_mean',contribution:2}]);
});
test('rejects nonnumeric and nonfinite contribution artifacts',()=>{
 for(const value of [null,[],{lag:NaN},{lag:'3'},{lag:Infinity}])expect(driverPoints(value)).toEqual([]);
});
