#import "PQStarsStore.h"

static NSString *const kKey = @"puzzlequest.stars";

@implementation PQStarsStore

+ (instancetype)sharedStore
{
    static PQStarsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQStarsStore alloc] init];
    });
    return shared;
}

- (NSInteger)total
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setTotal:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
