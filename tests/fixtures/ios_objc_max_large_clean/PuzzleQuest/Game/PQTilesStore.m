#import "PQTilesStore.h"

static NSString *const kKey = @"puzzlequest.tiles";

@implementation PQTilesStore

+ (instancetype)sharedStore
{
    static PQTilesStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQTilesStore alloc] init];
    });
    return shared;
}

- (NSInteger)cleared
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCleared:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
